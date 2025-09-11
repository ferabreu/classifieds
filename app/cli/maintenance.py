import os
import uuid
import click
from flask import current_app
from app.models import ListingImage, db

@click.command("backfill-thumbnails")
def backfill_thumbnails():
    """Generate thumbnails for existing images that don't have them."""
    from app.routes.utils import create_thumbnail

    images_without_thumbnails = ListingImage.query.filter(
        ListingImage.thumbnail_filename.is_(None)
    ).all()

    if not images_without_thumbnails:
        print("No images found that need thumbnail generation.")
        return

    print(f"Found {len(images_without_thumbnails)} images without thumbnails.")

    upload_dir = current_app.config["UPLOAD_DIR"]
    thumbnail_dir = current_app.config["THUMBNAIL_DIR"]

    success_count = 0
    error_count = 0

    for image in images_without_thumbnails:
        try:
            original_path = os.path.join(upload_dir, image.filename)
            if not os.path.exists(original_path):
                print(f"Warning: Original image not found: {image.filename}")
                error_count += 1
                continue

            thumbnail_filename = f"{uuid.uuid4().hex}.jpg"
            thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)

            if create_thumbnail(original_path, thumbnail_path):
                image.thumbnail_filename = thumbnail_filename
                db.session.add(image)
                success_count += 1
                print(f"Generated thumbnail for {image.filename}")
            else:
                print(f"Failed to generate thumbnail for {image.filename}")
                error_count += 1

        except Exception as e:
            print(f"Error processing {image.filename}: {e}")
            error_count += 1

    try:
        db.session.commit()
        print(f"\nThumbnail generation completed:")
        print(f"Successfully processed: {success_count}")
        print(f"Errors: {error_count}")
    except Exception as e:
        db.session.rollback()
        print(f"Error committing changes to database: {e}")