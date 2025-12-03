import os
import random
import re
import shutil
import time
from datetime import datetime

import click
import numpy as np
import requests
from dotenv import load_dotenv
from faker import Faker
from flask import current_app
from PIL import Image, ImageDraw, ImageFont

from app import db
from app.cli.maintenance import backfill_thumbnails
from app.models import Category, Listing, ListingImage, User

# ==========================
# CONFIGURABLE CONSTANTS
# ==========================
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
USER_EMAIL = "admin@classifieds.io"  # Email of the user to own all demo listings
USE_RANDOM_TITLES = False  # Toggle to use random titles (set to False for cache reuse, True for new Unsplash images)
MAX_UNSPLASH_IMAGES = 10  # Max Unsplash API calls per run
UNSPLASH_API_DELAY = 1.2  # Seconds to wait between Unsplash API calls
DEMO_IMAGES_FOLDER = "static/demo_images"
FALLBACK_IMAGE_COUNT = 8  # Ensure at least this many images exist
MIN_IMAGES_PER_LISTING = 1  # Minimum images per listing
MAX_IMAGES_PER_LISTING = 3  # Maximum images per listing
MIN_PRICE = 5.0
MAX_PRICE = 5000.0

# ==========================
# SUBCATEGORY KEYWORD MAPPING
# ==========================
# Map subcategory names to related keywords for Unsplash
SUBCATEGORY_KEYWORDS = {
    "Furniture": ["furniture", "table", "chair", "sofa", "desk", "couch", "cabinet"],
    "Phones": ["phone", "smartphone", "mobile", "cellphone", "iphone", "android"],
    "Computers": ["computer", "laptop", "desktop", "notebook", "pc", "macbook"],
    "Tools": ["tools", "hammer", "drill", "saw", "wrench", "toolbox"],
    "Cars": ["car", "automobile", "sedan", "convertible", "hatchback", "vehicle"],
    "Motorcycles": ["motorcycle", "bike", "scooter", "motorbike", "chopper"],
    "Clothing": ["clothing", "shirt", "pants", "dress", "jacket", "fashion"],
    "Shoes": ["shoes", "sneakers", "boots", "sandals", "footwear", "heels"],
}

fake = Faker()


def fetch_unsplash_image(
    query, dest_path, access_key=UNSPLASH_ACCESS_KEY, delay=UNSPLASH_API_DELAY
):
    """Fetches a random Unsplash image for a query and saves it to dest_path. Returns True if successful.
    Respects delay to avoid hitting API rate limits."""
    if not access_key:
        print("Unsplash API key not set. Skipping Unsplash fetch.")
        return False
    url = f"https://api.unsplash.com/photos/random?query={query}"
    headers = {"Authorization": f"Client-ID {access_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
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
    # Sanitize query to create a safe filename
    safe_query = re.sub(r"[^a-zA-Z0-9_\-]", "_", query.strip().replace(" ", "_"))
    # Limit filename length for safety
    safe_query = safe_query[:40]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"unsplash_{safe_query}_{timestamp}.jpg"


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
        if query is None:
            # Use cached images by matching keywords in the query (derived from listing title)
            cached_images = [
                f for f in os.listdir(folder) if f.lower().endswith(".jpg")
            ]
            if cached_images:
                fname = cached_images[i % len(cached_images)]
                # Extract keywords for message
                keywords = re.sub(r"^unsplash_", "", fname)
                keywords = re.sub(r"_[0-9]{8}_[0-9]{6}\.jpg$", "", keywords)
                keywords = keywords.replace("_", " ").strip()
                print(f"Copied cached image for '{keywords}'")
                filenames.append(fname)
            else:
                # If no cached images exist, generate a random one
                fname = f"random_{i+1}.jpg"
                generate_random_jpg(
                    os.path.join(folder, fname), text=fake.word().capitalize()
                )
                print(f"Generated random image for fallback: '{fname}'")
                filenames.append(fname)
        else:
            if unsplash_calls < max_unsplash_images:
                cache_fname = get_image_cache_filename(query)
                img_path = os.path.join(folder, cache_fname)
                if not os.path.exists(img_path):
                    fetch_success = fetch_unsplash_image(query, img_path)
                    unsplash_calls += 1  # Increment regardless of success or failure
                    # Only delay for actual API calls
                    if not fetch_success:
                        generate_random_jpg(img_path, text=query.capitalize())
                else:
                    # Extract keywords for message
                    keywords = re.sub(r"^unsplash_", "", cache_fname)
                    keywords = re.sub(r"_[0-9]{8}_[0-9]{6}\.jpg$", "", keywords)
                    keywords = keywords.replace("_", " ").strip()
                    print(f"Copied cached image for '{keywords}'")
                filenames.append(cache_fname)
            else:
                # Use random local image for overflow
                fname = f"demo_{i+1}.jpg"
                img_path = os.path.join(folder, fname)
                if not os.path.exists(img_path):
                    generate_random_jpg(img_path, text=query.capitalize())
                print(f"Generated random image for overflow: '{fname}'")
                filenames.append(fname)

    # Ensure at least fallback_count images exist
    existing = [f for f in os.listdir(folder) if f.lower().endswith(".jpg")]
    while len(existing) < fallback_count:
        fname = f"random_{len(existing)+1}.jpg"
        generate_random_jpg(os.path.join(folder, fname), text=fake.word().capitalize())
        existing.append(fname)
    # Return the list of filenames in order of listing queries
    return filenames


def get_or_create_categories():
    """Get existing categories/subcategories, or create if missing."""
    categories = Category.query.filter(Category.parent_id.is_(None)).all()  # type: ignore
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
    subcats = Category.query.filter(Category.parent_id.isnot(None)).all()  # type: ignore
    if not subcats:
        parent_map = {c.name: c for c in categories}
        subcats = [
            Category(name="Phones", parent_id=parent_map["Electronics"].id),
            Category(name="Computers", parent_id=parent_map["Electronics"].id),
            Category(name="Furniture", parent_id=parent_map["Home & Garden"].id),
            Category(name="Tools", parent_id=parent_map["Home & Garden"].id),
            Category(name="Cars", parent_id=parent_map["Vehicles"].id),
            Category(name="Motorcycles", parent_id=parent_map["Vehicles"].id),
            Category(name="Clothing", parent_id=parent_map["Fashion"].id),
            Category(name="Shoes", parent_id=parent_map["Fashion"].id),
        ]
        db.session.add_all(subcats)
        db.session.commit()
    return subcats


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
    # Load .env at command runtime (safe, minimal side effect)
    try:
        load_dotenv()
    except Exception:
        # If load_dotenv fails for any reason, continue without aborting the CLI
        pass

    thumbnail_dir = current_app.config["THUMBNAIL_DIR"]

    if replace:
        db.drop_all()
        db.create_all()
        print("All demo data cleared! Starting fresh.")

    # Get subcategories only
    subcats = get_or_create_categories()

    # Find the demo user
    demo_user = User.query.filter_by(email=USER_EMAIL).first()
    if not demo_user:
        print(f"ERROR: Demo user with email '{USER_EMAIL}' does not exist. Aborting.")
        return

    # Dynamically set number of listings per subcategory based on MAX_UNSPLASH_IMAGES
    demo_listings = []
    listing_queries = []
    # Generate fixed_titles from cached image filenames
    cached_images = [
        f
        for f in os.listdir(os.path.join(current_app.root_path, DEMO_IMAGES_FOLDER))
        if f.lower().endswith(".jpg")
    ]

    # Extract keywords from filenames (remove prefix, timestamp, extension)
    def extract_keywords(fname):
        base = re.sub(r"^unsplash_", "", fname)
        base = re.sub(r"_[0-9]{8}_[0-9]{6}\.jpg$", "", base)
        # Replace underscores with spaces
        return base.replace("_", " ").strip()

    fixed_titles = [extract_keywords(f) for f in cached_images]
    # Fallback if no cached images
    if not fixed_titles:
        fixed_titles = [
            "Vintage Camera",
            "Mountain Bike",
            "Leather Sofa",
            "Gaming Laptop",
            "Designer Shoes",
        ]
    original_titles = []
    num_subcategories = len(subcats)
    # Calculate listings per subcategory so total does not exceed MAX_UNSPLASH_IMAGES
    listings_per_subcategory = max(1, MAX_UNSPLASH_IMAGES // num_subcategories)
    remainder = MAX_UNSPLASH_IMAGES % num_subcategories
    for idx, cat in enumerate(subcats):
        n_listings = listings_per_subcategory + (1 if idx < remainder else 0)
        for i in range(n_listings):
            if USE_RANDOM_TITLES:
                # Use a keyword related to the subcategory for Unsplash
                keywords_list = SUBCATEGORY_KEYWORDS.get(cat.name, [cat.name])
                keyword = random.choice(keywords_list)
                title = f"{keyword.title()} {cat.name} #{i+1}"
                listing_queries.append(keyword)
            else:
                keywords = fixed_titles[i % len(fixed_titles)]
                title = f"{keywords} {cat.name} #{i+1}"
                original_titles.append(title)
                # Use keywords for cached image selection
                query_keywords = "_".join(keywords.split())
                listing_queries.append(query_keywords)
            description = fake.paragraph(nb_sentences=2)
            price = round(random.uniform(MIN_PRICE, MAX_PRICE), 2)
            listing = Listing(
                title=title,
                description=f"{description}\nPrice: ${price}",
                price=price,
                category_id=cat.id,
                user_id=demo_user.id,
            )
            db.session.add(listing)
            demo_listings.append(listing)
    # Run backfill_thumbnails at the end
    try:
        backfill_thumbnails()
    except Exception as e:
        print(f"Error running backfill_thumbnails: {e}")
    db.session.commit()

    # After creation, update fixed-title listings to append current date and time
    if not USE_RANDOM_TITLES:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for listing in demo_listings:
            # Only update if the title exactly matches an original fixed title (no datetime yet)
            if listing.title in original_titles:
                listing.title = f"{listing.title} [{now_str}]"
        db.session.commit()

    # Demo images: fetch from Unsplash only when using random titles
    src_folder = os.path.join(current_app.root_path, DEMO_IMAGES_FOLDER)
    dest_folder = os.path.join(current_app.root_path, current_app.config["UPLOAD_DIR"])
    os.makedirs(dest_folder, exist_ok=True)
    os.makedirs(thumbnail_dir, exist_ok=True)
    if USE_RANDOM_TITLES:
        image_files = ensure_demo_images(src_folder, queries=listing_queries)
        # Copy images to uploads folder
        for fname in image_files:
            src_path = os.path.join(src_folder, fname)
            dest_path = os.path.join(dest_folder, fname)
            shutil.copyfile(src_path, dest_path)
    else:
        # For fixed titles, just ensure fallback images exist
        image_files = ensure_demo_images(
            src_folder, queries=["demo" for _ in range(FALLBACK_IMAGE_COUNT)]
        )
        for fname in image_files:
            src_path = os.path.join(src_folder, fname)
            dest_path = os.path.join(dest_folder, fname)
            shutil.copyfile(src_path, dest_path)

    # Attach a random number of images to each listing
    for i, listing in enumerate(demo_listings):
        n_images = random.randint(MIN_IMAGES_PER_LISTING, MAX_IMAGES_PER_LISTING)
        for j in range(n_images):
            img_name = image_files[(i + j) % len(image_files)]
            db.session.add(ListingImage(listing_id=listing.id, filename=img_name))
    db.session.commit()

    print(
        f"Demo data seeded: categories, listings, images. {'(Tables replaced)' if replace else '(Added to existing data)'}"
    )
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
