import click
import os
import shutil
from flask import current_app
from app import db
from app.models import Category, Listing, ListingImage, User
from PIL import Image
import numpy as np
from faker import Faker
import random
import requests

fake = Faker()

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")


def fetch_unsplash_image(query, dest_path, access_key=UNSPLASH_ACCESS_KEY):
    """Fetches a random Unsplash image based on a query and saves it to dest_path."""
    url = f"https://api.unsplash.com/photos/random?query={query}&client_id={access_key}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            img_url = resp.json()['urls']['regular']
            img_data = requests.get(img_url, timeout=10).content
            with open(dest_path, 'wb') as f:
                f.write(img_data)
            print(f"Fetched Unsplash image for '{query}'")
            return True
        else:
            print(f"Unsplash API error: {resp.status_code} for '{query}'")
    except Exception as e:
        print(f"Error fetching Unsplash image for '{query}': {e}")
    return False

def generate_random_jpg(path, width=400, height=300, text=None):
    """Generates and saves a random jpg image at the given path, with optional text."""
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    if text:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        font_size = 32
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
        draw.text((10, 10), text, (255, 255, 255), font=font)
    img.save(path, format="JPEG")

def ensure_demo_images(folder, queries, fallback_count=8):
    """
    Download images from Unsplash for each query.
    If Unsplash fails, generate random images instead.
    Returns list of image filenames in the folder.
    """
    os.makedirs(folder, exist_ok=True)
    filenames = []
    for i, query in enumerate(queries):
        fname = f"demo_{i+1}.jpg"
        img_path = os.path.join(folder, fname)
        success = fetch_unsplash_image(query, img_path)
        if not success:
            generate_random_jpg(img_path, text=query.capitalize())
        filenames.append(fname)
    # If not enough images, fill with randoms
    existing = [f for f in os.listdir(folder) if f.lower().endswith('.jpg')]
    while len(existing) < fallback_count:
        fname = f"random_{len(existing)+1}.jpg"
        generate_random_jpg(os.path.join(folder, fname), text=fake.word().capitalize())
        existing.append(fname)
    return [f for f in os.listdir(folder) if f.lower().endswith('.jpg')]

def create_demo_users(count=5):
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

@click.command('demo-data')
def demo_data():
    """Seed demo categories, users, listings, and images with realistic data using Unsplash or random images."""
    db.drop_all()
    db.create_all()

    # Categories & subcategories
    categories = [
        Category(name="Electronics"),
        Category(name="Home & Garden"),
        Category(name="Vehicles"),
        Category(name="Fashion"),
    ]
    subcats = [
        Category(name="Phones", parent=categories[0]),
        Category(name="Computers", parent=categories[0]),
        Category(name="Furniture", parent=categories[1]),
        Category(name="Tools", parent=categories[1]),
        Category(name="Cars", parent=categories[2]),
        Category(name="Motorcycles", parent=categories[2]),
        Category(name="Clothing", parent=categories[3]),
        Category(name="Shoes", parent=categories[3]),
    ]
    db.session.add_all(categories + subcats)
    db.session.commit()

    # Demo users
    users = create_demo_users(count=5)

    # Demo listings (generate titles, descriptions, queries for images)
    listing_queries = []
    demo_listings = []
    for i in range(9):
        cat = random.choice(subcats)
        user = random.choice(users)
        title = fake.sentence(nb_words=4)
        description = fake.paragraph(nb_sentences=2)
        price = round(random.uniform(10, 5000), 2)
        listing = Listing(
            title=title,
            description=f"{description}\nPrice: ${price}",
            category=cat,
            user=user,
        )
        db.session.add(listing)
        demo_listings.append(listing)
        # Use category name or title for image search
        query = cat.name
        listing_queries.append(query)
    db.session.commit()

    # Demo images: fetch from Unsplash or generate random
    src_folder = os.path.join(current_app.root_path, 'static', 'demo_images')
    dest_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    image_files = ensure_demo_images(src_folder, queries=listing_queries)
    os.makedirs(dest_folder, exist_ok=True)
    # Copy images to uploads folder
    for fname in image_files:
        src_path = os.path.join(src_folder, fname)
        dest_path = os.path.join(dest_folder, fname)
        shutil.copyfile(src_path, dest_path)

    # Attach images to listings (one per listing)
    for i, listing in enumerate(demo_listings):
        img_name = image_files[i % len(image_files)]
        db.session.add(ListingImage(listing=listing, filename=img_name))
    db.session.commit()

    print("Realistic demo data seeded: categories, users, listings, images.")
    print("Demo user passwords: demopass")
    print("Images downloaded from Unsplash when possible, otherwise generated randomly.")
    print("Remember to set your Unsplash access key in app/cli/demo.py.")
