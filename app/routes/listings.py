# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot
at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Listings Blueprint routes for Flask app.

This module contains all listing-related routes including:
- Public listing views (index, category browsing, listing details)
- User listing management (create, edit, delete listings with images)
- Admin listing management (bulk operations, moderation)
- Image upload/thumbnail generation with atomic temp->commit->move pattern
- Category-based filtering and showcase displays
"""

import os
import random
import shutil
import uuid

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from ..forms import ListingForm
from ..models import Category, CategoryView, Listing, ListingImage, db
from .decorators import admin_required
from .utils import (
    cleanup_temp_files,
    create_thumbnail,
    get_index_carousel_categories,
    move_image_files_to_temp,
    restore_files_from_temp,
)

listings_bp = Blueprint("listings", __name__)


# -------------------- LISTINGS ROUTES -----------------------


@listings_bp.route("/")
def index():
    # Check if any categories exist (controls "+ Post New Listing" button visibility)
    any_categories_exist = db.session.execute(select(Category)).first() is not None

    # Get selected categories for carousels
    carousel_categories = get_index_carousel_categories()

    # Build carousel data: for each category, fetch listings and randomize
    items_per_carousel = current_app.config.get("INDEX_CAROUSEL_ITEMS_PER_CATEGORY", 10)
    # The UI shows up to 5 cards per row on ultrawide; fetch only what's useful
    display_slots = min(items_per_carousel, 5)
    # Fetch a bit extra for variety without over-querying
    fetch_limit = max(display_slots * 2, items_per_carousel)
    category_carousels = []
    for category in carousel_categories:
        # Prefer direct category listings first
        direct_listings = (
            db.session.execute(
                select(Listing)
                .where(Listing.category_id == category.id)  # type: ignore
                .order_by(Listing.created_at.desc())
                .limit(fetch_limit)
            )
            .scalars()
            .all()
        )

        listings_pool = list(direct_listings)

        # If not enough to fill the row, pull from descendants to fill gaps
        if len(listings_pool) < fetch_limit:
            descendant_ids = category.get_descendant_ids()
            descendant_ids = [cid for cid in descendant_ids if cid != category.id]
            if descendant_ids:
                needed = fetch_limit - len(listings_pool)
                descendant_listings = (
                    db.session.execute(
                        select(Listing)
                        .where(Listing.category_id.in_(descendant_ids))  # type: ignore
                        .order_by(Listing.created_at.desc())
                        .limit(
                            max(needed * 2, display_slots)
                        )  # small buffer for variety
                    )
                    .scalars()
                    .all()
                )
                listings_pool.extend(descendant_listings)

        if listings_pool:
            random.shuffle(listings_pool)
            listings = listings_pool[:display_slots]
            category_carousels.append({"category": category, "listings": listings})

    return render_template(
        "index.html",
        category_carousels=category_carousels,
        any_categories_exist=any_categories_exist,
        page_title="",
    )


@listings_bp.route("/category/<int:category_id>")
def category_listings(category_id):
    page = request.args.get("page", 1, type=int)
    per_page = 24

    category = db.get_or_404(Category, category_id)
    descendant_ids = category.get_descendant_ids()
    listings_query = select(Listing).where(Listing.category_id.in_(descendant_ids))  # type: ignore
    pagination = db.paginate(  # type: ignore
        listings_query.order_by(Listing.created_at.desc()),
        page=page,
        per_page=per_page,
        error_out=False,
    )
    listings = pagination.items

    category_path = category.get_full_path()

    # --- Sidebar context additions ---
    # 1. Get all root categories with their children (for sidebar)
    categories = (
        db.session.execute(
            select(Category).where(Category.parent_id.is_(None)).order_by(Category.name)  # type: ignore
        )
        .scalars()
        .all()
    )
    # 2. Compute ancestor IDs for expansion using breadcrumb property
    ancestor_ids = [cat.id for cat in category.breadcrumb[:-1]]
    expanded_ids = ancestor_ids  # List of IDs to auto-expand

    return render_template(
        "index.html",
        listings=listings,
        pagination=pagination,
        selected_category=category,
        category_path=category_path,
        categories=categories,  # <-- for sidebar macro
        active_category_id=category_id,
        expanded_ids=expanded_ids,
        page_title=category_path,
    )


@listings_bp.route("/<path:category_path>")
def category_filtered_listings(category_path):
    category = Category.from_path(category_path)
    if not category:
        abort(404)

    # --- Sidebar context additions ---
    # 1. Get all root categories with their children (for sidebar)
    categories = (
        db.session.execute(
            select(Category).where(Category.parent_id.is_(None)).order_by(Category.name)  # type: ignore
        )
        .scalars()
        .all()
    )
    # 2. Compute ancestor IDs for expansion using breadcrumb property
    ancestor_ids = [cat.id for cat in category.breadcrumb[:-1]]
    expanded_ids = ancestor_ids  # List of IDs to auto-expand

    # Check if user explicitly requested listings view (grid instead of showcases)
    view_mode = request.args.get("view", "auto")
    force_listings_view = view_mode == "listings"

    # Check if this is an intermediate category (has children) or a leaf category
    if category.children and not force_listings_view:
        # Intermediate category: show showcase of child categories
        items_per_carousel = current_app.config.get(
            "INDEX_CAROUSEL_ITEMS_PER_CATEGORY", 10
        )
        display_slots = min(items_per_carousel, 6)  # Up to 6 child categories
        fetch_limit = max(display_slots * 2, items_per_carousel)

        # Build showcases for each child category
        child_showcases = []
        for child_category in sorted(
            category.children, key=lambda c: c.name  # type: ignore[arg-type]
        ):
            # Fetch listings for this child
            direct_listings = (
                db.session.execute(
                    select(Listing)
                    .where(Listing.category_id == child_category.id)  # type: ignore
                    .order_by(Listing.created_at.desc())
                    .limit(fetch_limit)
                )
                .scalars()
                .all()
            )

            listings_pool = list(direct_listings)

            # If not enough, pull from descendants of this child
            if len(listings_pool) < fetch_limit:
                descendant_ids = child_category.get_descendant_ids()
                descendant_ids = [
                    cid for cid in descendant_ids if cid != child_category.id
                ]
                if descendant_ids:
                    needed = fetch_limit - len(listings_pool)
                    descendant_listings = (
                        db.session.execute(
                            select(Listing)
                            .where(Listing.category_id.in_(descendant_ids))  # type: ignore
                            .order_by(Listing.created_at.desc())
                            .limit(max(needed * 2, display_slots))
                        )
                        .scalars()
                        .all()
                    )
                    listings_pool.extend(descendant_listings)

            if listings_pool:
                random.shuffle(listings_pool)
                listings = listings_pool[:display_slots]
                child_showcases.append(
                    {"category": child_category, "listings": listings}
                )

        # Add showcase for listings directly in this intermediate category
        # (not in children)
        direct_category_listings = (
            db.session.execute(
                select(Listing)
                .where(Listing.category_id == category.id)  # type: ignore
                .order_by(Listing.created_at.desc())
                .limit(fetch_limit)
            )
            .scalars()
            .all()
        )

        if direct_category_listings:
            random.shuffle(direct_category_listings)
            other_category = CategoryView.from_category(
                category,
                name_override=f'Other {category.name}',
            )
            child_showcases.append(
                {
                    "category": other_category,
                    "listings": direct_category_listings[:display_slots],
                }
            )

        return render_template(
            "index.html",
            category_carousels=child_showcases,
            selected_category=category,
            category_path=category.get_full_path(),
            categories=categories,
            active_category_id=category.id,
            expanded_ids=expanded_ids,
            any_categories_exist=True,
            page_title=category.name,
        )
    else:
        # Leaf category or forced listings view:
        # show grid of all listings with pagination
        page = request.args.get("page", 1, type=int)
        per_page = 24

        descendant_ids = category.get_descendant_ids()
        listings_query = select(Listing).where(Listing.category_id.in_(descendant_ids))  # type: ignore
        pagination = db.paginate(  # type: ignore
            listings_query.order_by(Listing.created_at.desc()),
            page=page,
            per_page=per_page,
            error_out=False,
        )
        listings = pagination.items

        return render_template(
            "index.html",
            listings=listings,
            pagination=pagination,
            selected_category=category,
            category_path=category.get_full_path(),
            categories=categories,
            active_category_id=category.id,
            expanded_ids=expanded_ids,
            page_title=category.name,
        )


@listings_bp.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    category = listing.category
    category_path = category.get_full_path() if category else None

    return render_template(
        "listings/listing_detail.html",
        listing=listing,
        category=category,
        category_path=category_path,
        page_title=listing.title,
    )


@listings_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_listing():  # noqa: C901
    form = ListingForm()
    # For new listing, ensure category field is empty so JS shows only root dropdown
    if request.method == "GET":
        form.category.data = ""
    page_title = "New listing"

    temp_dir = current_app.config["TEMP_DIR"]

    if not temp_dir:
        flash("Temp directory is not configured.", "danger")
        return render_template(
            "listings/listing_form.html",
            form=form,
            action="Create",
            page_title=page_title,
        )
    if not os.path.exists(temp_dir):
        flash(
            "Temp directory does not exist. Please initialize the application.",
            "danger",
        )
        return render_template(
            "listings/listing_form.html",
            form=form,
            action="Create",
            page_title=page_title,
        )

    # Populate form category choices with hierarchical names, add blank option
    categories = (
        db.session.execute(select(Category).order_by(Category.name)).scalars().all()
    )
    form.category.choices = [("", "Select...")] + [
        (str(cat.id), cat.get_full_path()) for cat in categories
    ]  # type: ignore

    if request.method == "POST":
        form.category.choices = [("", "Select...")] + [
            (str(cat.id), cat.get_full_path())
            for cat in db.session.execute(
                select(Category).order_by(Category.name)
            ).scalars()
        ]  # type: ignore
        if form.validate_on_submit():
            # Convert category to int if selected
            category_id = int(form.category.data) if form.category.data else None
            # Backend checks for None on required fields (PyLance type safety)
            if form.title.data is None:
                flash(
                    "Title is missing. Please provide a title for your listing.",
                    "danger",
                )
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    action="Create",
                    page_title=page_title,
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
                    action="Create",
                    page_title=page_title,
                )
            if form.price.data is None:
                flash(
                    "Price is missing. Please provide a price for your listing.",
                    "danger",
                )
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    action="Create",
                    page_title=page_title,
                )
            if not category_id:
                flash(
                    "Category is missing. Please select a category for your listing.",
                    "danger",
                )
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    action="Create",
                    page_title=page_title,
                )
            listing = Listing(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data or 0,
                user_id=current_user.id,
                category_id=category_id,
            )

            added_temp_paths = []
            added_files = []

            # Store uploaded images in TEMP_DIR first
            if form.images.data:
                for file in form.images.data:
                    if file and file.filename:
                        ext = os.path.splitext(secure_filename(file.filename))[1]
                        unique_filename = f"{uuid.uuid4().hex}{ext}"
                        thumbnail_filename = f"{uuid.uuid4().hex}.jpg"
                        temp_path = os.path.join(temp_dir, unique_filename)
                        temp_thumb_path = os.path.join(temp_dir, thumbnail_filename)
                        file.save(temp_path)
                        # Create thumbnail
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
                                # Best-effort temp cleanup;
                                # failure is non-fatal but logged
                                current_app.logger.warning(
                                    "Temp remove failed (image): %s", cleanup_err
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
                                    # Best-effort temp cleanup;
                                    # failure is non-fatal but logged
                                    current_app.logger.warning(
                                        "Temp remove failed (previous image): %s",
                                        cleanup_err,
                                    )
                            flash(
                                f"Failed to create thumbnail for image "
                                f"'{file.filename}'. Please try again or use "
                                "a different image format.",
                                "danger",
                            )
                            return render_template(
                                "listings/listing_form.html",
                                form=form,
                                action="Create",
                                page_title=page_title,
                            )

            commit_success = False
            try:
                db.session.add(listing)
                db.session.flush()  # Assigns an id to listing
                for unique_filename, thumbnail_filename in added_files:
                    image = ListingImage(
                        filename=unique_filename,
                        thumbnail_filename=thumbnail_filename,
                        listing_id=listing.id,
                    )
                    db.session.add(image)
                db.session.commit()
                commit_success = True
            except Exception as e:
                db.session.rollback()
                for temp_path, _, temp_thumb_path, _ in added_temp_paths:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        if temp_thumb_path and os.path.exists(temp_thumb_path):
                            os.remove(temp_thumb_path)
                    except Exception as cleanup_err:
                        # Best-effort temp cleanup after rollback;
                        # failure is non-fatal but logged
                        current_app.logger.warning(
                            "Temp remove failed (rollback): %s", cleanup_err
                        )
                flash(
                    f"Database error. Listing was not created. "
                    f"Uploaded files were discarded. ({e})",
                    "danger",
                )
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    action="Create",
                    page_title=page_title,
                )

            if commit_success:
                upload_dir = current_app.config["UPLOAD_DIR"]
                thumbnail_dir = current_app.config["THUMBNAIL_DIR"]
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
                flash("Listing created successfully!", "success")
                return redirect(
                    url_for("listings.listing_detail", listing_id=listing.id)
                )
    return render_template(
        "listings/listing_form.html", form=form, action="Create", page_title=page_title
    )


@listings_bp.route("/delete/<int:listing_id>", methods=["POST"])
@login_required
def delete_listing(listing_id):
    return _delete_listing_impl(listing_id)


@listings_bp.route("/edit/<int:listing_id>", methods=["GET", "POST"])
@login_required
def edit_listing(listing_id):
    return _edit_listing_impl(listing_id)


# ---------------- ADMIN LISTINGS MANAGEMENT -----------------


@listings_bp.route("/admin/listings/delete/<int:listing_id>", methods=["POST"])
@admin_required
def admin_delete_listing(listing_id):
    return _delete_listing_impl(listing_id)


@listings_bp.route("/admin/listings/edit/<int:listing_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_listing(listing_id):
    return _edit_listing_impl(listing_id)


@listings_bp.route("/admin/listings")
@admin_required
def admin_listings():
    """Lists all listings (ordered by least recent) for admin management."""
    page = request.args.get("page", 1, type=int)
    sort = request.args.get("sort", "created_at")
    direction = request.args.get("direction", "desc")

    sort_column_map = {
        "title": Listing.title,
        "price": Listing.price,
        "category": Listing.category_id,
        "user": Listing.user_id,
        "created_at": Listing.created_at,
    }
    sort_column = sort_column_map.get(sort, Listing.created_at)
    sort_order = sort_column.asc() if direction == "asc" else sort_column.desc()

    pagination = db.paginate(  # type: ignore
        select(Listing).order_by(sort_order), page=page, per_page=20
    )
    listings = pagination.items

    return render_template(
        "admin/admin_listings.html",
        listings=listings,
        pagination=pagination,
        sort=sort,
        direction=direction,
        page_title="Manage listings",
    )


@listings_bp.route("/admin/listings/view/<int:listing_id>")
@admin_required
def admin_listing_detail(listing_id):
    return listing_detail(listing_id)


@listings_bp.route("/admin/listings/delete_selected", methods=["POST"])
@admin_required
def delete_selected_listings():
    """
    Deletes multiple selected listings and all their associated image files.
    """
    selected_ids = request.form.getlist("selected_listings")
    if not selected_ids:
        flash("No listings selected for deletion.", "warning")
        return redirect(url_for("listings.admin_listings"))

    listings = (
        db.session.execute(
            select(Listing)
            .options(joinedload(Listing.images))  # type: ignore
            .where(Listing.id.in_(selected_ids))  # type: ignore
        )
        .scalars()
        .unique()
        .all()
    )

    success, error_message, count = _delete_listings_impl(listings)

    if success:
        flash(f"Deleted {count} listing(s).", "success")
    else:
        flash(f"Error deleting listings: {error_message}", "danger")

    return redirect(url_for("listings.admin_listings"))


# -------------------- HELPER FUNCTIONS -----------------------


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
