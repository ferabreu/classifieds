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

# === Routes ===


@listings_bp.route("/")
def index():
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

    # --- Sidebar context additions ---
    # 1. Get all root categories with their children (for sidebar)
    categories = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
    # 2. Compute ancestor IDs for expansion
    from .utils import get_category_ancestor_ids  # Adjust import as needed

    ancestor_ids = get_category_ancestor_ids(categories, category_id) or []
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


@listings_bp.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
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
    form = ListingForm()
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

    # Populate form category choices with hierarchical names
    categories = Category.query.order_by(Category.name).all()
    form.category.choices = [(cat.id, cat.get_full_path()) for cat in categories]

    if request.method == "POST":
        form.category.choices = [
            (cat.id, cat.get_full_path())
            for cat in Category.query.order_by(Category.name)
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
                    action="Create",
                    page_title=page_title,
                )
            if form.description.data is None:
                flash(
                    "Description is missing. Please provide a description for your listing.",
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
            if form.category.data is None:
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
                            f"Warning: Could not finalize upload for {unique_filename}: {e}",
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
    categories = Category.query.order_by(Category.name).all()
    form = ListingForm()
    form.category.choices = [(cat.id, cat.get_full_path()) for cat in categories]

    if request.method == "POST":
        form.category.choices = [
            (cat.id, cat.get_full_path())
            for cat in Category.query.order_by(Category.name)
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
                    "Description is missing. Please provide a description for your listing.",
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
                    "Category is missing. Please select a category for your listing.",
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

            # Handle image deletions: move to temp, do not delete yet (enables rollback on DB error)
            delete_image_ids = request.form.getlist("delete_images")
            for img_id in delete_image_ids:
                image = ListingImage.query.get(int(img_id))
                if image and image in listing.images:
                    image_path = os.path.join(upload_dir, image.filename)
                    temp_path = os.path.join(temp_dir, image.filename)
                    thumbnail_path = None
                    temp_thumb_path = None
                    if image.thumbnail_filename:
                        thumbnail_path = os.path.join(
                            thumbnail_dir, image.thumbnail_filename
                        )
                        temp_thumb_path = os.path.join(
                            temp_dir, image.thumbnail_filename
                        )
                    try:
                        if os.path.exists(image_path):
                            shutil.move(image_path, temp_path)
                            moved_to_temp.append(
                                (image_path, temp_path, thumbnail_path, temp_thumb_path)
                            )
                        if (
                            thumbnail_path
                            and temp_thumb_path
                            and os.path.exists(thumbnail_path)
                            and os.path.exists(temp_thumb_path)
                        ):
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
                    final_path = os.path.join(upload_dir, unique_filename)
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
                            thumbnail_dir, thumbnail_filename
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
    listing = Listing.query.get_or_404(listing_id)
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

    original_paths = []
    temp_paths = []
    original_thumb_paths = []
    temp_thumb_paths = []

    for image in listing.images:
        orig = os.path.join(upload_dir, image.filename)
        temped = os.path.join(temp_dir, image.filename)
        orig_thumb = None
        temped_thumb = None
        if image.thumbnail_filename:
            orig_thumb = os.path.join(thumbnail_dir, image.thumbnail_filename)
            temped_thumb = os.path.join(temp_dir, image.thumbnail_filename)
        try:
            if os.path.exists(orig):
                shutil.move(orig, temped)
                original_paths.append(orig)
                temp_paths.append(temped)
                if (
                    orig_thumb
                    and temped_thumb
                    and os.path.exists(orig_thumb)
                    and os.path.exists(temped_thumb)
                ):
                    shutil.move(orig_thumb, temped_thumb)
                    original_thumb_paths.append(orig_thumb)
                    temp_thumb_paths.append(temped_thumb)
        except Exception as e:
            flash(f"Error moving image {image.filename} to temp: {e}", "warning")

    try:
        db.session.delete(listing)
        db.session.commit()
    except Exception as e:
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
