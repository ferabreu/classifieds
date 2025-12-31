# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Flask CLI commands for demo data generation.

Provides commands to populate the database with sample categories, users, and listings with images.
Includes smart category creation, realistic listing generation, and Unsplash image integration.
"""

import os
import random
import re
import shutil
import time
from datetime import datetime

import click

# import numpy as np
import requests
from dotenv import load_dotenv
from faker import Faker
from flask import current_app

from app import db
from app.cli.maintenance import run_backfill_thumbnails
from app.models import Category, Listing, ListingImage, User

# from PIL import Image, ImageDraw, ImageFont


# ==========================
# CONFIGURABLE CONSTANTS
# ==========================
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
USER_EMAIL = "admin@classifieds.io"  # Email of admin user (fallback if DISTRIBUTE_ACROSS_USERS is False)
DISTRIBUTE_ACROSS_USERS = True  # If True, distribute listings across all existing users; if False, assign all to admin
MAX_UNSPLASH_IMAGES = 50  # Max Unsplash API calls per run
UNSPLASH_API_DELAY = 1.2  # Seconds to wait between Unsplash API calls
DEMO_IMAGES_FOLDER = "static/demo_images"
FALLBACK_IMAGE_COUNT = 8  # Ensure at least this many images exist
MIN_IMAGES_PER_LISTING = 1  # Minimum images per listing
MAX_IMAGES_PER_LISTING = 2  # Maximum images per listing
MIN_PRICE = 5.0
MAX_PRICE = 5000.0
DEMO_MARKER = (
    "[DEMO]"  # Marker to identify demo-created listings without schema changes
)

# ==========================
# CATEGORY HIERARCHY
# ==========================
# Map parent category names to their subcategories
CATEGORY_HIERARCHY = {
    "Electronics": ["Phones", "Computers"],
    "Home & Garden": ["Furniture", "Tools"],
    "Vehicles": ["Cars", "Motorcycles"],
    "Fashion": ["Clothing", "Shoes"],
}

# ==========================
# SUBCATEGORY KEYWORD MAPPING
# ==========================
# Map subcategory names to related keywords for Unsplash
CATEGORY_KEYWORDS = {
    "Phones": ["phone", "smartphone", "mobile", "cellphone"],
    "Computers": ["computer", "laptop", "desktop", "notebook", "pc"],
    "Furniture": ["table", "chair", "sofa", "desk", "couch", "cabinet"],
    "Tools": [
        "screwdriver",
        "hammer",
        "drill",
        "saw",
        "wrench",
        "toolbox",
        "file",
        "sandpaper",
    ],
    "Cars": ["car", "automobile", "sedan", "convertible", "hatchback"],
    "Motorcycles": ["motorcycle", "scooter", "motorbike"],
    "Clothing": [
        "shirt",
        "pants",
        "dress",
        "jacket",
        "blouse",
        "jeans",
        "trousers",
        "hoodie",
    ],
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


def get_image_cache_filename(query):
    """Returns a filename for caching Unsplash images based on query string."""
    # Sanitize query to create a safe filename
    safe_query = re.sub(r"[^a-zA-Z0-9_\-]", "_", query.strip().replace(" ", "_"))
    # Limit filename length for safety
    safe_query = safe_query[:40]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"unsplash_{safe_query}_{timestamp}.jpg"


def find_cached_image(folder, query):
    """Find a cached image for the given query.

    Picks one at random among all matches of the form
    'unsplash_{safe_query}_*.jpg'. Returns the filename or None.
    """
    safe_query = re.sub(r"[^a-zA-Z0-9_\-]", "_", query.strip().replace(" ", "_"))
    safe_query = safe_query[:40]
    pattern = f"unsplash_{safe_query}_"

    if not os.path.exists(folder):
        return None

    matches = [
        fname
        for fname in os.listdir(folder)
        if fname.startswith(pattern) and fname.endswith(".jpg")
    ]
    if matches:
        return random.choice(matches)
    return None


def find_cached_images(folder, query):
    """Return all cached image filenames for a given query (may be empty)."""
    safe_query = re.sub(r"[^a-zA-Z0-9_\-]", "_", query.strip().replace(" ", "_"))
    safe_query = safe_query[:40]
    pattern = f"unsplash_{safe_query}_"

    if not os.path.exists(folder):
        return []

    return [
        fname
        for fname in os.listdir(folder)
        if fname.startswith(pattern) and fname.endswith(".jpg")
    ]


def ensure_demo_images(
    folder,
    queries,
    fallback_count=FALLBACK_IMAGE_COUNT,
    max_unsplash_images=MAX_UNSPLASH_IMAGES,
    cache_only=False,
):
    """
    For the first N queries, fetch from Unsplash (with caching, so repeated titles reuse images).
    For all others, generate random images.
    Returns list of image filenames (relative to folder).

    If cache_only=True, only reuse cached images and never fetch from Unsplash.
    """
    os.makedirs(folder, exist_ok=True)
    filenames = []
    unsplash_calls = 0

    for i, query in enumerate(queries):
        if query:
            if unsplash_calls < max_unsplash_images:
                # Check if we already have a cached image for this query
                cached_fname = find_cached_image(folder, query)

                if cached_fname:
                    # Reuse existing cached image
                    print(f"Reusing cached image for '{query}'")
                    filenames.append(cached_fname)
                elif not cache_only:
                    # Fetch new image from Unsplash (only if not cache-only mode)
                    cache_fname = get_image_cache_filename(query)
                    img_path = os.path.join(folder, cache_fname)
                    fetch_success = fetch_unsplash_image(query, img_path)
                    unsplash_calls += 1  # Increment regardless of success or failure
                    if fetch_success:
                        filenames.append(cache_fname)
                    else:
                        # No local random generation; skip image for this query
                        print(f"No image available for '{query}' (fetch failed).")
                else:
                    # Cache-only mode: skip if no cached image exists
                    print(f"No cached image for '{query}' (cache-only mode).")
            else:
                # Unsplash limit reached; do not generate local randoms
                print(f"Unsplash limit reached; skipping image for '{query}'.")

    # Return only the list of real filenames gathered for queries
    return filenames


def get_or_create_categories():
    """Get existing categories/subcategories from CATEGORY_HIERARCHY, or create if missing.

    Validates that SUBCATEGORY_KEYWORDS keys match the subcategories defined in CATEGORY_HIERARCHY.
    """
    # Validate SUBCATEGORY_KEYWORDS alignment
    expected_subcats = set()
    for subcats_list in CATEGORY_HIERARCHY.values():
        expected_subcats.update(subcats_list)

    keyword_keys = set(CATEGORY_KEYWORDS.keys())
    if keyword_keys != expected_subcats:
        missing_in_keywords = expected_subcats - keyword_keys
        extra_in_keywords = keyword_keys - expected_subcats
        if missing_in_keywords:
            print(
                f"WARNING: SUBCATEGORY_KEYWORDS missing entries for: {missing_in_keywords}"
            )
        if extra_in_keywords:
            print(
                f"WARNING: SUBCATEGORY_KEYWORDS has extra entries not in CATEGORY_HIERARCHY: {extra_in_keywords}"
            )

    # Get or create parent categories
    categories = Category.query.filter(Category.parent_id.is_(None)).all()  # type: ignore
    existing_parents = {c.name: c for c in categories}

    for parent_name in CATEGORY_HIERARCHY.keys():
        if parent_name not in existing_parents:
            parent = Category(name=parent_name)
            db.session.add(parent)
            db.session.flush()  # Get ID without full commit
            existing_parents[parent_name] = parent

    if db.session.new:
        db.session.commit()

    # Get or create subcategories
    subcats = Category.query.filter(Category.parent_id.isnot(None)).all()  # type: ignore
    existing_subcats = {c.name: c for c in subcats}

    for parent_name, subcat_names in CATEGORY_HIERARCHY.items():
        parent = existing_parents[parent_name]
        for subcat_name in subcat_names:
            if subcat_name not in existing_subcats:
                subcat = Category(name=subcat_name, parent_id=parent.id)
                db.session.add(subcat)
                db.session.flush()
                existing_subcats[subcat_name] = subcat

    if db.session.new:
        db.session.commit()

    # Return all subcategories (existing + newly created)
    return list(existing_subcats.values())


@click.command("demo-data")
@click.option(
    "--replace/--no-replace",
    default=False,
    help="Replace all demo data (drop and recreate tables).",
)
@click.option(
    "--images-only",
    is_flag=True,
    default=False,
    help="Fetch cached Unsplash images only (no listings or DB changes).",
)
@click.option(
    "--cache-only",
    is_flag=True,
    default=False,
    help="Use only cached images (do not fetch new images from Unsplash).",
)
def demo_data(replace, images_only, cache_only):
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

    # Images-only mode: fetch fresh images from Unsplash, skipping cache
    if images_only:
        src_folder = os.path.join(current_app.root_path, DEMO_IMAGES_FOLDER)
        os.makedirs(src_folder, exist_ok=True)

        # Flatten values (keywords) and cycle until MAX_UNSPLASH_IMAGES
        all_keywords = [kw for kws in CATEGORY_KEYWORDS.values() for kw in kws]
        image_queries = []
        idx = 0
        while len(image_queries) < MAX_UNSPLASH_IMAGES and all_keywords:
            image_queries.append(all_keywords[idx % len(all_keywords)])
            idx += 1

        # Fetch fresh images without checking cache
        fetched_count = 0
        unsplash_calls = 0
        for query in image_queries:
            if unsplash_calls < MAX_UNSPLASH_IMAGES:
                cache_fname = get_image_cache_filename(query)
                img_path = os.path.join(src_folder, cache_fname)
                if fetch_unsplash_image(query, img_path):
                    fetched_count += 1
                unsplash_calls += 1

        print(f"Fetched {fetched_count} fresh images to {src_folder}")
        print("No listings created due to --images-only.")
        return

    if replace:
        print(
            "Replacing demo listings: clearing demo listings/images only; preserving users and categories."
        )
        upload_dir = current_app.config["UPLOAD_DIR"]
        thumbnail_dir = current_app.config["THUMBNAIL_DIR"]

        # Identify demo listings by marker in description
        all_listings = Listing.query.all()
        demo_listings = [
            lst
            for lst in all_listings
            if (lst.description or "").find(DEMO_MARKER) != -1
        ]
        if not demo_listings:
            print("No demo listings found to replace.")
            return

        # Capture image records via relationship for file removal before DB deletion
        existing_images = []
        for lst in demo_listings:
            existing_images.extend(list(lst.images))
        try:
            # Delete demo listings using ORM to trigger cascade for images
            for lst in demo_listings:
                db.session.delete(lst)
            db.session.commit()
            print(
                f"Deleted {len(demo_listings)} demo listings (images removed via cascade)."
            )
        except Exception as e:
            db.session.rollback()
            print(f"ERROR: Failed to clear demo listings: {e}")
            return

        # Remove files on disk for previously recorded images
        removed_files = 0
        for img in existing_images:
            try:
                img_path = os.path.join(upload_dir, img.filename)
                if os.path.exists(img_path):
                    os.remove(img_path)
                    removed_files += 1
                if img.thumbnail_filename:
                    thumb_path = os.path.join(thumbnail_dir, img.thumbnail_filename)
                    if os.path.exists(thumb_path):
                        os.remove(thumb_path)
                        removed_files += 1
            except Exception:
                # Continue on individual file errors
                pass
        print(f"Removed {removed_files} files from uploads/thumbnails.")

    # Get subcategories only
    subcats = get_or_create_categories()

    # Get users for listing assignment
    if DISTRIBUTE_ACROSS_USERS:
        demo_users = User.query.all()
        if not demo_users:
            print(f"ERROR: No users exist in the database. Aborting.")
            return
        print(f"Distributing listings across {len(demo_users)} existing users.")
    else:
        demo_user = User.query.filter_by(email=USER_EMAIL).first()
        if not demo_user:
            print(
                f"ERROR: Demo user with email '{USER_EMAIL}' does not exist. Aborting."
            )
            return
        demo_users = [demo_user]

    # Build listings from SUBCATEGORY_KEYWORDS values only (query terms), mapped to their category keys
    demo_listings = []
    listing_queries = []
    listing_keywords = []  # Track per-listing keyword for semantic image attachment
    user_index = 0  # For round-robin user assignment
    demo_folder_path = os.path.join(current_app.root_path, DEMO_IMAGES_FOLDER)

    # Map subcategory name -> Category object for assignment
    subcat_map = {c.name: c for c in subcats}

    # Flatten all (keyword, category_name) pairs from SUBCATEGORY_KEYWORDS
    keyword_pairs = []
    for cat_name, keywords_list in CATEGORY_KEYWORDS.items():
        for kw in keywords_list:
            keyword_pairs.append((kw, cat_name))

    # Shuffle to randomly distribute listings across all keywords
    random.shuffle(keyword_pairs)

    # Create listings without exceeding Unsplash API limit (cap by images per listing)
    listings_limit = (
        MAX_UNSPLASH_IMAGES // MAX_IMAGES_PER_LISTING if MAX_IMAGES_PER_LISTING else 0
    )
    total_listings = listings_limit if keyword_pairs else 0

    # Helper function to generate realistic product titles
    def generate_product_title(keyword, category_name):
        """Generate realistic product-like titles using keyword + descriptors."""
        adjectives = [
            "Premium",
            "Professional",
            "Classic",
            "Modern",
            "Deluxe",
            "Compact",
            "Portable",
            "Heavy-Duty",
            "Ultra",
            "Pro",
            "Elite",
            "Standard",
            "Advanced",
            "Essential",
            "Durable",
            "Sleek",
            "Elegant",
            "Rugged",
            "Eco-Friendly",
            "Smart",
        ]
        brands = [
            "TechPro",
            "ProHome",
            "MaxPower",
            "EcoStyle",
            "SmartLiving",
            "PrestigePlus",
            "FutureGen",
            "ClassicCraft",
            "ModernLiving",
            "VersaMax",
        ]

        # Randomly choose between brand-based or adjective-based title
        if random.choice([True, False]):
            # Brand + keyword style: "TechPro Smartphone"
            brand = random.choice(brands)
            title = f"{brand} {keyword.title()}"
        else:
            # Adjective + keyword style: "Premium Smartphone"
            adjective = random.choice(adjectives)
            title = f"{adjective} {keyword.title()}"

        return title

    for i in range(total_listings):
        kw, cat_name = keyword_pairs[i % len(keyword_pairs)]
        keyword = kw
        category = subcat_map.get(cat_name)
        if not category:
            # If category is missing, create it under no parent to avoid failure
            category = Category(name=cat_name)
            db.session.add(category)
            db.session.flush()  # get id without full commit
            subcat_map[cat_name] = category

        # Title and description
        title = generate_product_title(keyword, cat_name)
        # Add keyword multiple times to listing_queries to fetch multiple images per keyword
        for _ in range(MAX_IMAGES_PER_LISTING):
            listing_queries.append(keyword)
        listing_keywords.append(keyword)
        description = f"High-quality {keyword}. {fake.paragraph(nb_sentences=2)} Great for {cat_name} enthusiasts.\n{DEMO_MARKER}"
        price = round(random.uniform(MIN_PRICE, MAX_PRICE), 2)

        # Assign user in round-robin fashion
        assigned_user = demo_users[user_index % len(demo_users)]
        user_index += 1

        listing = Listing(
            title=title,
            description=description,
            price=price,
            category_id=category.id,
            user_id=assigned_user.id,
        )
        db.session.add(listing)
        demo_listings.append(listing)

    # Commit listings to database (assigns IDs)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"ERROR: Failed to create listings: {e}")
        return

    # Demo images: fetch/reuse Unsplash images for keyword queries
    src_folder = os.path.join(current_app.root_path, DEMO_IMAGES_FOLDER)
    dest_folder = os.path.join(current_app.root_path, current_app.config["UPLOAD_DIR"])
    os.makedirs(dest_folder, exist_ok=True)
    os.makedirs(thumbnail_dir, exist_ok=True)

    # Build/refresh cache; returns only real images (no randoms)
    image_files = ensure_demo_images(
        src_folder, queries=listing_queries, cache_only=cache_only
    )
    # Optional eager copy to uploads for the ones we have
    for fname in image_files:
        src_path = os.path.join(src_folder, fname)
        dest_path = os.path.join(dest_folder, fname)
        if os.path.exists(src_path) and not os.path.exists(dest_path):
            shutil.copyfile(src_path, dest_path)

    # Attach images to each listing - match images to listing's own query for semantic correspondence
    attachments_created = 0
    for i, listing in enumerate(demo_listings):
        n_images = random.randint(MIN_IMAGES_PER_LISTING, MAX_IMAGES_PER_LISTING)
        query = listing_keywords[i] if i < len(listing_keywords) else None

        selected_filenames = []
        if query:
            query_cached = find_cached_images(src_folder, query)
            if query_cached:
                take = min(n_images, len(query_cached))
                selected_filenames = random.sample(query_cached, take)

        # Ensure selected files exist in uploads (copy on-demand), then attach
        for img_name in selected_filenames:
            src_path = os.path.join(src_folder, img_name)
            dest_path = os.path.join(dest_folder, img_name)
            if os.path.exists(src_path) and not os.path.exists(dest_path):
                try:
                    shutil.copyfile(src_path, dest_path)
                except Exception:
                    continue
            db.session.add(ListingImage(listing_id=listing.id, filename=img_name))
            attachments_created += 1

    # Commit image associations
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"ERROR: Failed to attach images to listings: {e}")
        return

    # Run backfill_thumbnails AFTER images are attached
    if attachments_created:
        try:
            print("Running thumbnail backfill for new images...")
            run_backfill_thumbnails()
        except Exception as e:
            print(f"Warning: Error running backfill_thumbnails: {e}")
    else:
        print("No images attached; skipping thumbnail backfill.")

    print(
        f"Demo data seeded: categories, listings, images. {'(Listings replaced)' if replace else '(Added to existing data)'}"
    )

    print(
        f"Up to {MAX_UNSPLASH_IMAGES} images requested from Unsplash (cached locally)."
    )

    print(
        f"Each listing gets between {MIN_IMAGES_PER_LISTING} and {MAX_IMAGES_PER_LISTING} images."
    )

    print(f"Thumbnails generated in {thumbnail_dir} using the shared utility.")

    if UNSPLASH_ACCESS_KEY is None:
        print(
            "Set UNSPLASH_ACCESS_KEY environment variable before running for best results."
        )
