# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Shared route utilities for the classifieds Flask app.

This module contains shared decorators and utility functions for use by multiple route Blueprints.
Currently, it provides the admin_required decorator for restricting access to admin users.
"""

import random

from flask import Blueprint, current_app
from PIL import Image
from sqlalchemy import func

from app.models import Category, Listing, db

utils_bp = Blueprint("utils", __name__)


def get_index_carousel_categories():
    """
    Retrieve up to N categories for displaying in index page carousels.

    Strategy:
    - If INDEX_CAROUSEL_CATEGORIES is explicitly configured, use those category IDs
      (filtered to only include categories with listings).
    - Otherwise, query top 2N categories by listing count, randomly select N from them,
      and filter out categories with no listings.

    Returns:
        list: Up to N Category objects with listings, in no particular order.
              Empty list if no categories with listings exist.
    """
    carousel_count = current_app.config.get("INDEX_CAROUSEL_COUNT", 4)
    explicit_categories = current_app.config.get("INDEX_CAROUSEL_CATEGORIES")

    if explicit_categories:
        # Use explicitly configured category IDs, filtered to only those with listings
        categories = Category.query.filter(
            Category.id.in_(explicit_categories),
            Category.listings.any(),
        ).all()
        return categories[:carousel_count]

    # Auto-select: query top 2N categories by listing count
    top_count = carousel_count * 2
    category_listing_counts = (
        db.session.query(
            Category.id,
            func.count(Listing.id).label("listing_count"),
        )
        .outerjoin(Listing)
        .group_by(Category.id)
        .order_by(func.count(Listing.id).desc())
        .limit(top_count)
        .all()
    )

    # Extract category IDs from results (only those with at least 1 listing)
    category_ids = [cat_id for cat_id, count in category_listing_counts if count > 0]

    # Randomly select up to N from the top 2N
    selected_ids = random.sample(category_ids, min(carousel_count, len(category_ids)))

    # Fetch and return the selected categories
    selected_categories = Category.query.filter(Category.id.in_(selected_ids)).all()

    return selected_categories


def create_thumbnail(image_path, thumbnail_path):
    """
    Create a thumbnail from an image file.

    Args:
        image_path (str): Path to the original image
        thumbnail_path (str): Path where the thumbnail will be saved
        size (tuple): Thumbnail size (width, height)

    Returns:
        bool: True if thumbnail was created successfully, False otherwise
    """
    size = current_app.config["THUMBNAIL_SIZE"]

    try:
        with Image.open(image_path) as img:
            # Convert palette images (P mode) with transparency to RGBA
            if img.mode == "P":
                img = img.convert("RGBA")
            # For all other images, convert to RGB if not already RGBA/RGB
            elif img.mode not in ("RGBA", "RGB"):
                img = img.convert("RGB")

            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Create a new image with the exact size and paste the thumbnail centered
            thumbnail = Image.new("RGB", size, color="white")

            # Calculate position to center the thumbnail
            x = (size[0] - img.size[0]) // 2
            y = (size[1] - img.size[1]) // 2

            thumbnail.paste(img, (x, y))

            # Save the thumbnail
            thumbnail.save(thumbnail_path, "JPEG", quality=85)
            return True
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return False
