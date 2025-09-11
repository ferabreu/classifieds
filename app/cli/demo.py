import click
from flask import current_app
from app import db
from app.models import Category, Listing, ListingImage
import os
import shutil

def create_demo_images():
    # Path to sample images (put a few .jpg files here)
    src_folder = os.path.join(current_app.root_path, 'static', 'demo_images')
    dest_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(dest_folder, exist_ok=True)
    image_files = [f for f in os.listdir(src_folder) if f.lower().endswith('.jpg')]
    for fname in image_files:
        shutil.copy(os.path.join(src_folder, fname), os.path.join(dest_folder, fname))
    return image_files

@click.command('demo-data')
def demo_data():
    """Load demo categories, subcategories, listings, and images."""
    db.drop_all()
    db.create_all()

    # Categories & Subcategories
    electronics = Category(name="Electronics")
    phones = Category(name="Phones", parent=electronics)
    laptops = Category(name="Laptops", parent=electronics)
    furniture = Category(name="Furniture")
    chairs = Category(name="Chairs", parent=furniture)

    db.session.add_all([electronics, phones, laptops, furniture, chairs])
    db.session.commit()

    # Listings
    images = create_demo_images()
    listing1 = Listing(title="iPhone 12", description="Like new!", category=phones)
    listing2 = Listing(title="MacBook Pro", description="2019 model", category=laptops)
    listing3 = Listing(title="Office Chair", description="Ergonomic", category=chairs)

    db.session.add_all([listing1, listing2, listing3])
    db.session.commit()

    # Attach images
    if images:
        db.session.add(ListingImage(listing=listing1, filename=images[0]))
        if len(images) > 1:
            db.session.add(ListingImage(listing=listing2, filename=images[1]))
        if len(images) > 2:
            db.session.add(ListingImage(listing=listing3, filename=images[2]))
        db.session.commit()

    print("Demo data loaded! Visit the app to see categories, subcategories, and sample listings.")
