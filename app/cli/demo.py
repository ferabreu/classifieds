import hashlib
import os
import random
import shutil
import time

import click
import numpy as np
import requests
from faker import Faker
from flask import current_app
from PIL import Image

from app import db
from app.models import Category, Listing, ListingImage, User
from app.routes.utils import create_thumbnail  # Use the shared thumbnail utility!

# ==========================
# CONFIGURABLE CONSTANTS
# ==========================
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")

N_USERS = 5
MIN_LISTINGS_PER_SUBCATEGORY = 3
MAX_LISTINGS_PER_SUBCATEGORY = 9
MAX_UNSPLASH_IMAGES = 10  # Max Unsplash API calls per run
UNSPLASH_API_DELAY = 1.2  # Seconds to wait between Unsplash API calls
DEMO_IMAGES_FOLDER = "static/demo_images"
UPLOAD_IMAGES_FOLDER = "static/uploads"
FALLBACK_IMAGE_COUNT = 8  # Ensure at least this many images exist

MIN_IMAGES_PER_LISTING = 1  # Minimum images per listing
MAX_IMAGES_PER_LISTING = 3  # Maximum images per listing

# Optional: load from .env if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

fake = Faker()


def fetch_unsplash_image(
    query, dest_path, access_key=UNSPLASH_ACCESS_KEY, delay=UNSPLASH_API_DELAY
):
    """Fetches a random Unsplash image for a query and saves it to dest_path. Returns True if successful.
    Respects delay to avoid hitting API rate limits."""
    if not access_key:
        print("Unsplash API key not set. Skipping Unsplash fetch.")
        return False
    url = f"https://api.unsplash.com/photos/random?query={query}&client_id={access_key}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200 and "urls" in resp.json():
            img_url = resp.json()["urls"]["regular"]
            img_data = requests.get(img_url, timeout=10).content
            with open(dest_path, "wb") as f:
                f.write(img_data)
            print(f"Fetched Unsplash image for '{query}'")
            time.sleep(delay)  # Be kind to the API
            return True
        else:
            print(f"Unsplash API error: {resp.status_code} for '{query}'")
    except Exception as e:
        print(f"Error fetching Unsplash image for '{query}': {e}")
    return False


def generate_random_jpg(path, width=400, height=300, text=None):
    """Generates and saves a random jpg image at the given path, with optional text."""
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    if text:
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(img)
        font_size = 32
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
        draw.text((10, 10), text[:20], (255, 255, 255), font=font)
    img.save(path, format="JPEG")


def get_image_cache_filename(query):
    """Returns a filename for caching Unsplash images based on query string."""
    key = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
    return f"unsplash_{key}.jpg"


def ensure_demo_images(
    folder,
    queries,
    fallback_count=FALLBACK_IMAGE_COUNT,
    max_unsplash_images=MAX_UNSPLASH_IMAGES,
):
    """
    For the first N queries, fetch from Unsplash (with caching, so repeated titles reuse images).
    For all others, generate random images.
    Returns list of image filenames (relative to folder).
    """
    os.makedirs(folder, exist_ok=True)
    filenames = []
    unsplash_calls = 0

    for i, query in enumerate(queries):
        if unsplash_calls < max_unsplash_images:
            cache_fname = get_image_cache_filename(query)
            img_path = os.path.join(folder, cache_fname)
            if not os.path.exists(img_path):
                if fetch_unsplash_image(query, img_path):
                    unsplash_calls += 1
                else:
                    generate_random_jpg(img_path, text=query.capitalize())
            else:
                print(f"Using cached Unsplash image for '{query}'")
            filenames.append(cache_fname)
        else:
            # Use random local image for overflow
            fname = f"demo_{i+1}.jpg"
            img_path = os.path.join(folder, fname)
            if not os.path.exists(img_path):
                generate_random_jpg(img_path, text=query.capitalize())
            filenames.append(fname)

    # Ensure at least fallback_count images exist
    existing = [f for f in os.listdir(folder) if f.lower().endswith(".jpg")]
    while len(existing) < fallback_count:
        fname = f"random_{len(existing)+1}.jpg"
        generate_random_jpg(os.path.join(folder, fname), text=fake.word().capitalize())
        existing.append(fname)
    # Return the list of filenames in order of listing queries
    return filenames


def create_demo_users(count=N_USERS):
    """Creates and commits demo users, returns them."""
    users = []
    for i in range(count):
        user = User(
            email=fake.unique.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            is_admin=(i == 0),
            is_ldap_user=False,
        )
        user.set_password("demopass")
        users.append(user)
    db.session.add_all(users)
    db.session.commit()
    return users


def get_or_create_categories():
    """Get existing categories/subcategories, or create if missing."""
    categories = Category.query.filter(Category.parent_id == None).all()
    if not categories:
        categories = [
            Category(name="Electronics"),
            Category(name="Home & Garden"),
            Category(name="Vehicles"),
            Category(name="Fashion"),
        ]
        db.session.add_all(categories)
        db.session.commit()
    # Get subcategories for each
    subcats = Category.query.filter(Category.parent_id != None).all()
    if not subcats:
        parent_map = {c.name: c for c in categories}
        subcats = [
            Category(name="Phones", parent=parent_map["Electronics"]),
            Category(name="Computers", parent=parent_map["Electronics"]),
            Category(name="Furniture", parent=parent_map["Home & Garden"]),
            Category(name="Tools", parent=parent_map["Home & Garden"]),
            Category(name="Cars", parent=parent_map["Vehicles"]),
            Category(name="Motorcycles", parent=parent_map["Vehicles"]),
            Category(name="Clothing", parent=parent_map["Fashion"]),
            Category(name="Shoes", parent=parent_map["Fashion"]),
        ]
        db.session.add_all(subcats)
        db.session.commit()
    categories = Category.query.filter(Category.parent_id == None).all()
    subcats = Category.query.filter(Category.parent_id != None).all()
    return categories, subcats


@click.command("demo-data")
@click.option(
    "--replace/--no-replace",
    default=False,
    help="Replace all demo data (drop and recreate tables).",
)
def demo_data(replace):
    """
    Seed demo categories, users, listings, and images with realistic data using Unsplash or random images (cached).
    By default, adds more data each run. Use --replace to remove all and start fresh.
    """
    thumbnail_dir = current_app.config["THUMBNAIL_DIR"]
    thumbnail_size = current_app.config["THUMBNAIL_SIZE"]

    if replace:
        db.drop_all()
        db.create_all()
        print("All demo data cleared! Starting fresh.")

    # Categories & subcategories
    categories, subcats = get_or_create_categories()

    # Demo users
    users = create_demo_users(count=N_USERS)

    # Demo listings: random number per subcategory (adds more each run!)
    demo_listings = []
    listing_queries = []
    for cat in subcats:
        num_listings = random.randint(
            MIN_LISTINGS_PER_SUBCATEGORY, MAX_LISTINGS_PER_SUBCATEGORY
        )
        for _ in range(num_listings):
            user = random.choice(users)
            title = fake.sentence(nb_words=random.randint(3, 6)).replace(".", "")
            description = fake.paragraph(nb_sentences=2)
            price = round(random.uniform(10, 5000), 2)
            listing = Listing(
                title=title,
                description=f"{description}\nPrice: ${price}",
                category_id=cat.id,
                user_id=user.id,
            )
            db.session.add(listing)
            demo_listings.append(listing)
            listing_queries.append(title)
    db.session.commit()

    # Demo images: fetch from Unsplash for a limited number, cache locally, generate random for the rest
    src_folder = os.path.join(current_app.root_path, DEMO_IMAGES_FOLDER)
    dest_folder = os.path.join(current_app.root_path, UPLOAD_IMAGES_FOLDER)
    image_files = ensure_demo_images(src_folder, queries=listing_queries)
    os.makedirs(dest_folder, exist_ok=True)
    os.makedirs(thumbnail_dir, exist_ok=True)
    # Copy images to uploads folder and generate thumbnails using shared create_thumbnail
    for fname in image_files:
        src_path = os.path.join(src_folder, fname)
        dest_path = os.path.join(dest_folder, fname)
        thumb_path = os.path.join(thumbnail_dir, fname)
        shutil.copyfile(src_path, dest_path)
        # Use the shared thumbnail function for consistency
        create_thumbnail(dest_path, thumb_path)

    # Attach a random number of images to each listing
    for i, listing in enumerate(demo_listings):
        n_images = random.randint(MIN_IMAGES_PER_LISTING, MAX_IMAGES_PER_LISTING)
        for j in range(n_images):
            img_name = image_files[(i + j) % len(image_files)]
            db.session.add(ListingImage(listing=listing, filename=img_name))
    db.session.commit()

    print(
        f"Demo data seeded: categories, users, listings, images. {'(Tables replaced)' if replace else '(Added to existing data)'}"
    )
    print(f"Demo user passwords: demopass")
    print(
        f"Up to {MAX_UNSPLASH_IMAGES} images downloaded from Unsplash (cached locally), rest generated randomly."
    )
    print(
        f"Each listing gets between {MIN_IMAGES_PER_LISTING} and {MAX_IMAGES_PER_LISTING} images."
    )
    print(f"Thumbnails generated in {thumbnail_dir} using the shared utility.")
    print(
        "Set UNSPLASH_ACCESS_KEY environment variable before running for best results."
    )
