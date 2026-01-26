# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
Helper functions for the Listings Blueprint.

This module contains reusable helper functions for listing operations:
- Showcase category selection and building
- Listing deletion with ACID file operations
- Listing editing with atomic temp->commit->move pattern
"""

import os
import random
import shutil
import uuid

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func, select
from werkzeug.utils import secure_filename

from app.forms import ListingForm
from app.models import Category, Listing, ListingImage, db

from ..utils import (
    cleanup_temp_files,
    create_thumbnail,
    move_image_files_to_temp,
    restore_files_from_temp,
)


def get_index_showcase_categories():
    """
    Retrieve up to N categories for displaying in index page showcases.

    Strategy:
    - If INDEX_CAROUSEL_CATEGORIES is explicitly configured, use those category IDs
      (filtered to only include categories with listings).
    - Otherwise, query top 2N categories by listing count, randomly select N from them,
      and filter out categories with no listings.

    Returns:
        list: Up to N Category objects with listings, in no particular order.
              Empty list if no categories with listings exist.

    Note: Config keys still use "CAROUSEL" naming for backward compatibility.
          These will be renamed to "SHOWCASE" in a future refactor.
    """
    showcase_count = current_app.config.get("INDEX_CAROUSEL_COUNT", 4)
    explicit_categories = current_app.config.get("INDEX_CAROUSEL_CATEGORIES")

    if explicit_categories:
        # Use explicitly configured category IDs, filtered to only those with listings
        categories = (
            db.session.execute(
                select(Category).where(
                    Category.id.in_(explicit_categories),
                    Category.listings.any(),
                )
            )
            .scalars()
            .all()
        )
        return categories[:showcase_count]

    # Auto-select: query top 2N categories by listing count
    top_count = showcase_count * 2
    category_listing_counts = db.session.execute(
        select(
            Category.id,
            func.count(Listing.id).label("listing_count"),
        )
        .outerjoin(Listing)
        .group_by(Category.id)
        .order_by(func.count(Listing.id).desc())
        .limit(top_count)
    ).all()

    # Extract category IDs from results (only those with at least 1 listing)
    category_ids = [cat_id for cat_id, count in category_listing_counts if count > 0]

    # Randomly select up to N from the top 2N
    selected_ids = random.sample(category_ids, min(showcase_count, len(category_ids)))

    # Fetch and return the selected categories
    selected_categories = (
        db.session.execute(select(Category).where(Category.id.in_(selected_ids)))
        .scalars()
        .all()
    )

    return selected_categories


def _delete_listings_impl(listings):
    """
    Deletes multiple listings and their associated image files using
    the 'temp' strategy.

    Args:
        listings: List of Listing objects to delete

    Returns:
        Tuple of (success: bool, error_message: str or None, count: int)
        - success: True if deletion completed without errors
        - error_message: Error message if deletion failed, None otherwise
        - count: Number of listings deleted
    """
    if not listings:
        return True, None, 0

    temp_dir = current_app.config["TEMP_DIR"]
    upload_dir = current_app.config["UPLOAD_DIR"]
    thumbnail_dir = current_app.config["THUMBNAIL_DIR"]

    # Collect all images from all listings
    all_images = []
    for listing in listings:
        all_images.extend(listing.images)

    # Move all image files to temp directory
    file_moves, success, error_msg = move_image_files_to_temp(
        all_images, upload_dir, thumbnail_dir, temp_dir
    )
    if not success:
        return False, error_msg, 0

    # Delete listings from database
    try:
        for listing in listings:
            db.session.delete(listing)
        db.session.commit()
    except Exception as e:
        # Rollback: restore all files
        restore_files_from_temp(file_moves)
        db.session.rollback()
        return False, f"Database error: {e}", 0

    # Clean up temp files
    cleanup_temp_files(file_moves)

    return True, None, len(listings)


def _delete_listing_impl(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    category = listing.category
    category_path = category.get_full_path() if category else None

    if current_user.id != listing.user_id and not current_user.is_admin:
        flash("You do not have permission to delete this listing.", "danger")
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )

    temp_dir = current_app.config["TEMP_DIR"]
    upload_dir = current_app.config["UPLOAD_DIR"]
    thumbnail_dir = current_app.config["THUMBNAIL_DIR"]

    if not temp_dir:
        flash("Temp directory is not configured.", "danger")
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )
    if not os.path.exists(temp_dir):
        flash(
            "Temp directory does not exist. Please initialize the application.",
            "danger",
        )
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )

    # Move images to temp
    file_moves, success, error_msg = move_image_files_to_temp(
        listing.images, upload_dir, thumbnail_dir, temp_dir
    )
    if not success:
        flash(f"Error moving images: {error_msg}", "warning")
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )

    # Delete listing from database
    try:
        db.session.delete(listing)
        db.session.commit()
    except Exception as e:
        # Rollback: restore all files
        restore_files_from_temp(file_moves)
        db.session.rollback()
        flash(
            f"Database error. Listing was not deleted. Files restored. ({e})", "danger"
        )
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )

    # Clean up temp files
    cleanup_temp_files(file_moves)

    flash(f"Listing deleted successfully! (Category: {category_path})", "success")
    if request.path.startswith("/admin") and current_user.is_admin:
        return redirect(url_for("listings.admin_listings"))
    return redirect(url_for("listings.index"))


def _edit_listing_impl(listing_id):  # noqa: C901
    listing = db.get_or_404(Listing, listing_id)
    page_title = "Edit listing"
    category = listing.category
    category_path = category.get_full_path() if category else None

    # Permission check: only owner or admin allowed
    if current_user.id != listing.user_id and not current_user.is_admin:
        flash("You do not have permission to edit this listing.", "danger")
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )

    temp_dir = current_app.config["TEMP_DIR"]

    if not temp_dir:
        flash("Temp directory is not configured.", "danger")
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )
    if not os.path.exists(temp_dir):
        flash(
            "Temp directory does not exist. Please initialize the application.",
            "danger",
        )
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )

    # Populate form choices
    categories = (
        db.session.execute(select(Category).order_by(Category.name)).scalars().all()
    )
    form = ListingForm()
    form.category.choices = [(cat.id, cat.get_full_path()) for cat in categories]

    if request.method == "POST":
        form.category.choices = [
            (cat.id, cat.get_full_path())
            for cat in db.session.execute(
                select(Category).order_by(Category.name)
            ).scalars()
        ]
        if form.validate_on_submit():
            # Backend checks for None on required fields (PyLance type safety)
            if form.title.data is None:
                flash(
                    "Title is missing. Please provide a title for your listing.",
                    "danger",
                )
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    listing=listing,
                    action="Edit",
                    page_title=page_title,
                    category=category,
                    category_path=category_path,
                )
            if form.description.data is None:
                flash(
                    "Description is missing. Please provide a description "
                    "for your listing.",
                    "danger",
                )
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    listing=listing,
                    action="Edit",
                    page_title=page_title,
                    category=category,
                    category_path=category_path,
                )
            if form.price.data is None:
                flash(
                    "Price is missing. Please provide a price for your listing.",
                    "danger",
                )
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    listing=listing,
                    action="Edit",
                    page_title=page_title,
                    category=category,
                    category_path=category_path,
                )
            if form.category.data is None:
                flash(
                    "Category is missing. Please select a category for "
                    "your listing.",
                    "danger",
                )
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    listing=listing,
                    action="Edit",
                    page_title=page_title,
                    category=category,
                    category_path=category_path,
                )
            listing.title = form.title.data
            listing.description = form.description.data
            listing.price = form.price.data or 0
            listing.category_id = form.category.data

            moved_to_temp = []
            added_temp_paths = []
            added_files = []

            upload_dir = current_app.config["UPLOAD_DIR"]
            thumbnail_dir = current_app.config["THUMBNAIL_DIR"]

            # Handle image deletions: move to temp, do not delete yet
            # (enables rollback on DB error)
            delete_image_ids = request.form.getlist("delete_images")
            images_to_delete = []
            for img_id in delete_image_ids:
                image = ListingImage.query.get(int(img_id))
                if image and image in listing.images:
                    images_to_delete.append(image)
                    db.session.delete(image)

            # Move images marked for deletion to temp
            moved_to_temp, success, error_msg = move_image_files_to_temp(
                images_to_delete, upload_dir, thumbnail_dir, temp_dir
            )
            if not success:
                flash(f"Error moving images to temp: {error_msg}", "warning")
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    listing=listing,
                    action="Edit",
                    page_title=page_title,
                    category=category,
                    category_path=category_path,
                )

            # Handle new image uploads: stage in TEMP_DIR until DB commit
            if form.images.data:
                for file in form.images.data:
                    if file and file.filename:
                        ext = os.path.splitext(secure_filename(file.filename))[1]
                        unique_filename = f"{uuid.uuid4().hex}{ext}"
                        thumbnail_filename = f"{uuid.uuid4().hex}.jpg"
                        temp_path = os.path.join(temp_dir, unique_filename)
                        temp_thumb_path = os.path.join(temp_dir, thumbnail_filename)
                        file.save(temp_path)
                        if create_thumbnail(temp_path, temp_thumb_path):
                            added_temp_paths.append(
                                (
                                    temp_path,
                                    unique_filename,
                                    temp_thumb_path,
                                    thumbnail_filename,
                                )
                            )
                            added_files.append((unique_filename, thumbnail_filename))
                        else:
                            try:
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)
                                if os.path.exists(temp_thumb_path):
                                    os.remove(temp_thumb_path)
                            except Exception as cleanup_err:
                                # Best-effort temp cleanup; failure is
                                # non-fatal but logged
                                current_app.logger.warning(
                                    "Temp remove failed (image during edit): %s",
                                    cleanup_err,
                                )
                            for (
                                prev_temp_path,
                                _,
                                prev_temp_thumb_path,
                                _,
                            ) in added_temp_paths:
                                try:
                                    if os.path.exists(prev_temp_path):
                                        os.remove(prev_temp_path)
                                    if prev_temp_thumb_path and os.path.exists(
                                        prev_temp_thumb_path
                                    ):
                                        os.remove(prev_temp_thumb_path)
                                except Exception as cleanup_err:
                                    # Best-effort temp cleanup; failure is
                                    # non-fatal but logged
                                    current_app.logger.warning(
                                        "Temp remove failed (prev image during "
                                        "edit): %s",
                                        cleanup_err,
                                    )
                            # Restore files that were moved to temp
                            restore_files_from_temp(moved_to_temp)
                            flash(
                                f"Failed to create thumbnail for image "
                                f"'{file.filename}'. Please try again or use "
                                f"a different image format.",
                                "danger",
                            )
                            return render_template(
                                "listings/listing_form.html",
                                form=form,
                                listing=listing,
                                action="Edit",
                                page_title=page_title,
                                category=category,
                                category_path=category_path,
                            )

            commit_success = False
            try:
                for unique_filename, thumbnail_filename in added_files:
                    image = ListingImage(
                        filename=unique_filename,
                        listing_id=listing.id,
                        thumbnail_filename=thumbnail_filename,
                    )
                    db.session.add(image)
                db.session.commit()
                commit_success = True
            except Exception as e:
                db.session.rollback()
                # Restore files that were moved to temp (deleted images)
                restore_files_from_temp(moved_to_temp)
                # Clean up temp files for newly added images
                cleanup_temp_files(added_temp_paths)
                flash(
                    f"Database error. Changes not saved. Files restored. ({e})",
                    "danger",
                )
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    listing=listing,
                    action="Save",
                    page_title=page_title,
                    category=category,
                    category_path=category_path,
                )

            if commit_success:
                # Clean up temp files for deleted images
                cleanup_temp_files(moved_to_temp)
                # Move newly added images from temp to final location
                for (
                    temp_path,
                    unique_filename,
                    temp_thumb_path,
                    thumbnail_filename,
                ) in added_temp_paths:
                    final_path = os.path.join(upload_dir, unique_filename)
                    try:
                        if os.path.exists(temp_path):
                            shutil.move(temp_path, final_path)
                    except Exception as e:
                        flash(
                            f"Warning: Could not finalize upload for "
                            f"{unique_filename}: {e}",
                            "warning",
                        )
                    if temp_thumb_path and thumbnail_filename:
                        final_thumb_path = os.path.join(
                            thumbnail_dir, thumbnail_filename
                        )
                        try:
                            if os.path.exists(temp_thumb_path):
                                shutil.move(temp_thumb_path, final_thumb_path)
                        except Exception as e:
                            flash(
                                f"Warning: Could not finalize thumbnail for "
                                f"{thumbnail_filename}: {e}",
                                "warning",
                            )
                flash("Listing updated successfully!", "success")
                if request.path.startswith("/admin") and current_user.is_admin:
                    return redirect(url_for("listings.admin_listings"))
                return redirect(
                    url_for("listings.listing_detail", listing_id=listing.id)
                )
    else:
        form.title.data = listing.title
        form.category.data = str(listing.category_id)
        form.description.data = listing.description
        form.price.data = listing.price

    return render_template(
        "listings/listing_form.html",
        form=form,
        listing=listing,
        action="Edit",
        page_title=page_title,
        category=category,
        category_path=category_path,
    )
