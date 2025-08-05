# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
#
"""
Routes for listings management in the classifieds Flask app.

Implements ACID-like file handling for listing image uploads and deletions:
- Images are first moved to a temp directory until DB commits succeed,
  ensuring DB and storage consistency even on errors.
- Only listing owners or admins can edit/delete listings.
"""

import os
import shutil
import uuid

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from ..forms import ListingForm
from ..models import Category, Listing, ListingImage, db
from .utils import create_thumbnail

listings_bp = Blueprint("listings", __name__)

# === Configuration values ===
# These are set from Flask app config for file storage directories.
UPLOAD_DIR = current_app.config["UPLOAD_DIR"]
TEMP_DIR = current_app.config["TEMP_DIR"]
THUMBNAIL_DIR = current_app.config["THUMBNAIL_DIR"]

# === Routes ===


@listings_bp.route("/")
def index():
    """
    Display all listings, newest first, paginated.
    """
    page = request.args.get("page", 1, type=int)
    per_page = 24  # Fits the grid layout in the UI
    pagination = Listing.query.order_by(Listing.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    listings = pagination.items

    return render_template(
        "index.html",
        listings=listings,
        pagination=pagination,
        page_title="All listings",
    )


@listings_bp.route("/category/<int:category_id>")
def category_listings(category_id):
    """
    Display listings filtered by category and its descendants.

    Uses Category.get_descendant_ids() to include all subcategories.
    """
    page = request.args.get("page", 1, type=int)
    per_page = 24

    category = Category.query.get_or_404(category_id)
    descendant_ids = category.get_descendant_ids()
    listings_query = Listing.query.filter(Listing.category_id.in_(descendant_ids))
    pagination = listings_query.order_by(Listing.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    listings = pagination.items

    category_path = category.get_full_path()

    return render_template(
        "index.html",
        listings=listings,
        pagination=pagination,
        selected_category=category,
        category_path=category_path,
        page_title=category_path,
    )


@listings_bp.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    """
    Display details for a single listing.

    Shows category path (breadcrumb) for navigation context.
    """
    listing = Listing.query.get_or_404(listing_id)
    category = listing.category
    category_path = category.get_full_path() if category else None

    return render_template(
        "listings/listing_detail.html",
        listing=listing,
        category=category,
        category_path=category_path,
        page_title=listing.title,
    )


@listings_bp.route("/subcategories_for_parent/<int:parent_id>")
@login_required
def subcategories_for_parent(parent_id):
    """
    Returns a JSON list of subcategories for a given parent category.
    Used for dynamic form population (AJAX/chained selects).
    """
    subcategories = (
        Category.query.filter_by(parent_id=parent_id).order_by(Category.name).all()
    )
    data = [
        {"id": subcat.id, "name": subcat.get_full_path()} for subcat in subcategories
    ]
    return jsonify(data)


@listings_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_listing():
    """
    Create a new listing with ACID-like file handling using TEMP_DIR.

    Steps:
    - Display form.
    - Validate submission.
    - Stage image files in TEMP_DIR.
    - On DB commit success, move images/thumbnails to final directory.
    - On DB failure, remove staged files.
    """
    form = ListingForm()
    page_title = "New listing"

    # Defensive: Temp directory must be configured and exist
    if not TEMP_DIR:
        flash("Temp directory is not configured.", "danger")
        return render_template(
            "listings/listing_form.html",
            form=form,
            action="Create",
            page_title=page_title,
        )
    if not os.path.exists(TEMP_DIR):
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

    # Populate form category choices with hierarchical names
    categories = Category.query.order_by(Category.name).all()
    form.category.choices = [(cat.id, cat.get_full_path()) for cat in categories]

    if request.method == "POST":
        form.category.choices = [
            (cat.id, cat.get_full_path())
            for cat in Category.query.order_by(Category.name)
        ]
        if form.validate_on_submit():
            listing = Listing(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data or 0,
                user_id=current_user.id,
                category_id=form.category.data,
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
                        temp_path = os.path.join(TEMP_DIR, unique_filename)
                        temp_thumb_path = os.path.join(TEMP_DIR, thumbnail_filename)
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
                            # Thumbnail creation failed: clean up staged files and abort
                            try:
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)
                                if os.path.exists(temp_thumb_path):
                                    os.remove(temp_thumb_path)
                            except Exception:
                                pass
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
                                except Exception:
                                    pass
                            flash(
                                f"Failed to create thumbnail for image '{file.filename}'. Please try again or use a different image format.",
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
                # Add listing and images to DB
                db.session.add(listing)
                for unique_filename, thumbnail_filename in added_files:
                    image = ListingImage(
                        filename=unique_filename,
                        thumbnail_filename=thumbnail_filename,
                        listing=listing,
                    )
                    db.session.add(image)
                db.session.commit()
                commit_success = True
            except Exception as e:
                # DB commit failed: rollback and clean up staged files
                db.session.rollback()
                for temp_path, _, temp_thumb_path, _ in added_temp_paths:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        if temp_thumb_path and os.path.exists(temp_thumb_path):
                            os.remove(temp_thumb_path)
                    except Exception:
                        pass
                flash(
                    f"Database error. Listing was not created. Uploaded files were discarded. ({e})",
                    "danger",
                )
                return render_template(
                    "listings/listing_form.html",
                    form=form,
                    action="Create",
                    page_title=page_title,
                )

            if commit_success:
                # Move staged files to permanent storage
                for (
                    temp_path,
                    unique_filename,
                    temp_thumb_path,
                    thumbnail_filename,
                ) in added_temp_paths:
                    final_path = os.path.join(UPLOAD_DIR, unique_filename)
                    try:
                        if os.path.exists(temp_path):
                            shutil.move(temp_path, final_path)
                    except Exception as e:
                        flash(
                            f"Warning: Could not finalize upload for {unique_filename}: {e}",
                            "warning",
                        )
                    if temp_thumb_path and thumbnail_filename:
                        final_thumb_path = os.path.join(
                            THUMBNAIL_DIR, thumbnail_filename
                        )
                        try:
                            if os.path.exists(temp_thumb_path):
                                shutil.move(temp_thumb_path, final_thumb_path)
                        except Exception as e:
                            flash(
                                f"Warning: Could not finalize thumbnail for {thumbnail_filename}: {e}",
                                "warning",
                            )
                flash("Listing created successfully!", "success")
                return redirect(
                    url_for("listings.listing_detail", listing_id=listing.id)
                )
    return render_template(
        "listings/listing_form.html", form=form, action="Create", page_title=page_title
    )


@listings_bp.route("/edit/<int:listing_id>", methods=["GET", "POST"])
@login_required
def edit_listing(listing_id):
    """
    Edit an existing listing with ACID-like file handling using TEMP_DIR.

    Steps:
    - Only owner or admin can edit.
    - Deleted images are moved to temp before DB commit.
    - New images are staged in temp before DB commit.
    - On DB failure, all file changes are rolled back.
    - On DB success, files are permanently changed.
    """
    listing = Listing.query.get_or_404(listing_id)
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

    # Defensive: Temp directory must be configured and exist
    if not TEMP_DIR:
        flash("Temp directory is not configured.", "danger")
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )
    if not os.path.exists(TEMP_DIR):
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
    categories = Category.query.order_by(Category.name).all()
    form = ListingForm()
    form.category.choices = [(cat.id, cat.get_full_path()) for cat in categories]

    if request.method == "POST":
        form.category.choices = [
            (cat.id, cat.get_full_path())
            for cat in Category.query.order_by(Category.name)
        ]
        if form.validate_on_submit():
            # Update listing fields
            listing.title = form.title.data
            listing.description = form.description.data
            listing.price = form.price.data or 0
            listing.category_id = form.category.data

            moved_to_temp = []
            added_temp_paths = []
            added_files = []

            # Handle image deletions: move to temp, do not delete yet (enables rollback on DB error)
            delete_image_ids = request.form.getlist("delete_images")
            for img_id in delete_image_ids:
                image = ListingImage.query.get(int(img_id))
                if image and image in listing.images:
                    image_path = os.path.join(UPLOAD_DIR, image.filename)
                    temp_path = os.path.join(TEMP_DIR, image.filename)
                    thumbnail_path = None
                    temp_thumb_path = None
                    if image.thumbnail_filename:
                        thumbnail_path = os.path.join(
                            THUMBNAIL_DIR, image.thumbnail_filename
                        )
                        temp_thumb_path = os.path.join(
                            TEMP_DIR, image.thumbnail_filename
                        )
                    try:
                        if os.path.exists(image_path):
                            shutil.move(image_path, temp_path)
                            moved_to_temp.append(
                                (image_path, temp_path, thumbnail_path, temp_thumb_path)
                            )
                        if thumbnail_path and os.path.exists(thumbnail_path):
                            shutil.move(thumbnail_path, temp_thumb_path)
                        db.session.delete(image)
                    except Exception as e:
                        flash(
                            f"Error moving image {image.filename} to temp: {e}",
                            "warning",
                        )

            # Handle new image uploads: stage in TEMP_DIR until DB commit
            if form.images.data:
                for file in form.images.data:
                    if file and file.filename:
                        ext = os.path.splitext(secure_filename(file.filename))[1]
                        unique_filename = f"{uuid.uuid4().hex}{ext}"
                        thumbnail_filename = f"{uuid.uuid4().hex}.jpg"
                        temp_path = os.path.join(TEMP_DIR, unique_filename)
                        temp_thumb_path = os.path.join(TEMP_DIR, thumbnail_filename)
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
                            # Thumbnail creation failed: clean up staged files and restore deleted images
                            try:
                                if os.path.exists(temp_path):
                                    os.remove(temp_path)
                                if os.path.exists(temp_thumb_path):
                                    os.remove(temp_thumb_path)
                            except Exception:
                                pass
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
                                except Exception:
                                    pass
                            for (
                                orig_path,
                                temp_path,
                                thumbnail_path,
                                temp_thumb_path,
                            ) in moved_to_temp:
                                try:
                                    if os.path.exists(temp_path):
                                        shutil.move(temp_path, orig_path)
                                    if temp_thumb_path and os.path.exists(
                                        temp_thumb_path
                                    ):
                                        shutil.move(temp_thumb_path, thumbnail_path)
                                except Exception:
                                    pass
                            flash(
                                f"Failed to create thumbnail for image '{file.filename}'. Please try again or use a different image format.",
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
                # Add new images to DB and commit changes
                for unique_filename, thumbnail_filename in added_files:
                    image = ListingImage(
                        filename=unique_filename,
                        thumbnail_filename=thumbnail_filename,
                        listing=listing,
                    )
                    db.session.add(image)
                db.session.commit()
                commit_success = True
            except Exception as e:
                # DB commit failed: restore deleted images and clean up staged files
                db.session.rollback()
                for (
                    orig_path,
                    temp_path,
                    thumbnail_path,
                    temp_thumb_path,
                ) in moved_to_temp:
                    try:
                        if os.path.exists(temp_path):
                            shutil.move(temp_path, orig_path)
                        if temp_thumb_path and os.path.exists(temp_thumb_path):
                            shutil.move(temp_thumb_path, thumbnail_path)
                    except Exception:
                        pass
                for temp_path, _, temp_thumb_path, _ in added_temp_paths:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        if temp_thumb_path and os.path.exists(temp_thumb_path):
                            os.remove(temp_thumb_path)
                    except Exception:
                        pass
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
                # Finalize file deletions and move new images to permanent storage
                for _, temp_path, _, temp_thumb_path in moved_to_temp:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        if temp_thumb_path and os.path.exists(temp_thumb_path):
                            os.remove(temp_thumb_path)
                    except Exception:
                        pass
                for (
                    temp_path,
                    unique_filename,
                    temp_thumb_path,
                    thumbnail_filename,
                ) in added_temp_paths:
                    final_path = os.path.join(UPLOAD_DIR, unique_filename)
                    try:
                        if os.path.exists(temp_path):
                            shutil.move(temp_path, final_path)
                    except Exception as e:
                        flash(
                            f"Warning: Could not finalize upload for {unique_filename}: {e}",
                            "warning",
                        )
                    if temp_thumb_path and thumbnail_filename:
                        final_thumb_path = os.path.join(
                            THUMBNAIL_DIR, thumbnail_filename
                        )
                        try:
                            if os.path.exists(temp_thumb_path):
                                shutil.move(temp_thumb_path, final_thumb_path)
                        except Exception as e:
                            flash(
                                f"Warning: Could not finalize thumbnail for {thumbnail_filename}: {e}",
                                "warning",
                            )
                flash("Listing updated successfully!", "success")
                return redirect(
                    url_for("listings.listing_detail", listing_id=listing.id)
                )
    else:
        # On GET: populate form fields from current listing
        form.title.data = listing.title
        form.category.data = listing.category_id
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


@listings_bp.route("/delete/<int:listing_id>", methods=["POST"])
@login_required
def delete_listing(listing_id):
    """
    Delete a listing and its images with ACID-like safety.

    Steps:
    - Only owner or admin can delete.
    - Images are moved to TEMP_DIR before DB commit.
    - On DB failure, images are restored.
    - On DB success, images are deleted from temp.
    """
    listing = Listing.query.get_or_404(listing_id)
    category = listing.category
    category_path = category.get_full_path() if category else None

    # Permission check
    if current_user.id != listing.user_id and not current_user.is_admin:
        flash("You do not have permission to delete this listing.", "danger")
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )

    # Defensive: Temp directory must be configured and exist
    if not TEMP_DIR:
        flash("Temp directory is not configured.", "danger")
        return render_template(
            "listings/listing_detail.html",
            listing=listing,
            category=category,
            category_path=category_path,
            page_title=listing.title,
        )
    if not os.path.exists(TEMP_DIR):
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

    original_paths = []
    temp_paths = []
    original_thumb_paths = []
    temp_thumb_paths = []

    # Move images to TEMP_DIR; only delete after DB commit
    for image in listing.images:
        orig = os.path.join(UPLOAD_DIR, image.filename)
        temped = os.path.join(TEMP_DIR, image.filename)
        orig_thumb = None
        temped_thumb = None
        if image.thumbnail_filename:
            orig_thumb = os.path.join(THUMBNAIL_DIR, image.thumbnail_filename)
            temped_thumb = os.path.join(TEMP_DIR, image.thumbnail_filename)
        try:
            if os.path.exists(orig):
                shutil.move(orig, temped)
                original_paths.append(orig)
                temp_paths.append(temped)
                if orig_thumb and os.path.exists(orig_thumb):
                    shutil.move(orig_thumb, temped_thumb)
                    original_thumb_paths.append(orig_thumb)
                    temp_thumb_paths.append(temped_thumb)
        except Exception as e:
            flash(f"Error moving image {image.filename} to temp: {e}", "warning")

    try:
        # Delete listing from DB (cascade deletes images)
        db.session.delete(listing)
        db.session.commit()
    except Exception as e:
        # DB commit failed: restore images from TEMP_DIR
        for orig, temped in zip(original_paths, temp_paths):
            try:
                if os.path.exists(temped):
                    shutil.move(temped, orig)
            except Exception:
                pass
        for orig_thumb, temped_thumb in zip(original_thumb_paths, temp_thumb_paths):
            try:
                if os.path.exists(temped_thumb):
                    shutil.move(temped_thumb, orig_thumb)
            except Exception:
                pass
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

    # DB commit succeeded: images can be deleted from TEMP_DIR
    for temped in temp_paths:
        try:
            if os.path.exists(temped):
                os.remove(temped)
        except Exception:
            pass
    for temped_thumb in temp_thumb_paths:
        try:
            if os.path.exists(temped_thumb):
                os.remove(temped_thumb)
        except Exception:
            pass

    flash(f"Listing deleted successfully! (Category: {category_path})", "success")
    return redirect(url_for("listings.index"))
