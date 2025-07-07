# Created by GitHub Copilot for Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu)

from flask import Blueprint, current_app, flash, g, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from ..forms import ListingForm
from ..models import db, Category, Listing, ListingImage, Type
import os, shutil, uuid

listings_bp = Blueprint('listings', __name__)

@listings_bp.route('/')
def index():
    """Show all listings, newest first."""
    listings = Listing.query.order_by(Listing.created_at.desc()).all()
    return render_template('index.html', listings=listings)

@listings_bp.route('/type/<int:type_id>')
def by_type(type_id):
    """Show listings filtered by type."""
    listings = Listing.query.filter_by(type_id=type_id).order_by(Listing.created_at.desc()).all()
    selected_type = Type.query.get_or_404(type_id)
    return render_template('index.html', listings=listings, selected_type=selected_type)

@listings_bp.route('/type/<int:type_id>/category/<int:category_id>')
def by_type_category(type_id, category_id):
    """Show listings filtered by type and category."""
    listings = Listing.query.filter_by(type_id=type_id, category_id=category_id).order_by(Listing.created_at.desc()).all()
    selected_type = Type.query.get_or_404(type_id)
    selected_category = Category.query.get_or_404(category_id)
    return render_template('index.html', listings=listings, selected_type=selected_type, selected_category=selected_category)

@listings_bp.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    """Show details for a single listing."""
    listing = Listing.query.get_or_404(listing_id)
    return render_template('listing_detail.html', listing=listing)

@listings_bp.route('/categories_for_type/<int:type_id>')
@login_required
def categories_for_type(type_id):
    """
    Returns a JSON list of categories for a given type. Used for dynamic form population.
    """
    categories = Category.query.filter_by(type_id=type_id).order_by(Category.name).all()
    category_list = [{'id': c.id, 'name': c.name} for c in categories]
    return jsonify(category_list)

@listings_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_listing():
    """
    Create a new listing with ACID-like file handling using TEMP_DIR.
    - On GET: show empty form.
    - On POST: validate and save listing and images using atomic file/database logic.
    - Uploaded images are first saved to TEMP_DIR.
    - If DB commit succeeds, move images from TEMP_DIR to UPLOAD_DIR.
    - If DB commit fails, delete images from TEMP_DIR.
    - On success: redirect to detail page of the new listing (not index).
    """
    form = ListingForm()
    
    if not current_app.config['TEMP_DIR']:
        flash('Temp directory is not configured.', 'danger')
        return render_template("listing_form.html", form=form, action="Create")
    
    if not os.path.exists(current_app.config['TEMP_DIR']):
        flash('Temp directory does not exist. Please initialize the application.', 'danger')
        return render_template("listing_form.html", form=form, action="Create")
        
    types = Type.query.order_by(Type.name).all()
    
    form.type.choices = [(t.id, t.name) for t in types]
    # Default to first type's categories
    categories = Category.query.filter_by(type_id=types[0].id).all() if types else []
    form.category.choices = [(c.id, c.name) for c in categories]
    if request.method == 'POST':
        # Update choices for type/category dropdowns in form
        form.type.choices = [(t.id, t.name) for t in Type.query.order_by(Type.name)]
        form.category.choices = [
            (c.id, c.name) for c in Category.query.filter_by(type_id=form.type.data).order_by(Category.name)
        ]
        if form.validate_on_submit():
            listing = Listing(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data or 0,
                user_id=current_user.id,
                type_id=form.type.data,
                category_id=form.category.data
            )

            upload_dir = current_app.config['UPLOAD_DIR']
            temp_dir = current_app.config['TEMP_DIR']
            
            added_temp_paths = []
            added_files = []

            # --- Save uploaded images to temp (not final location) ---
            if form.images.data:
                for file in form.images.data:
                    if file and file.filename:
                        ext = os.path.splitext(secure_filename(file.filename))[1]
                        unique_filename = f"{uuid.uuid4().hex}{ext}"
                        temp_path = os.path.join(temp_dir, unique_filename)
                        file.save(temp_path)
                        added_temp_paths.append((temp_path, unique_filename))
                        added_files.append(unique_filename)

            commit_success = False
            try:
                # Add listing and new images to DB but don't move to final location yet
                db.session.add(listing)
                for unique_filename in added_files:
                    image = ListingImage(filename=unique_filename, listing=listing)
                    db.session.add(image)
                db.session.commit()
                commit_success = True
            except Exception as e:
                db.session.rollback()
                # Remove any temp-uploaded files
                for temp_path, _ in added_temp_paths:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception:
                        pass
                flash(f"Database error. Listing was not created. Uploaded files were discarded. ({e})", "danger")
                return render_template("listing_form.html", form=form, action="Create")
            
            # --- If commit succeeded: finalize file system changes ---
            if commit_success:
                # Move new images from temp to upload dir
                for temp_path, unique_filename in added_temp_paths:
                    final_path = os.path.join(upload_dir, unique_filename)
                    try:
                        if os.path.exists(temp_path):
                            shutil.move(temp_path, final_path)
                    except Exception as e:
                        flash(f"Warning: Could not finalize upload for {unique_filename}: {e}", "warning")

                flash('Listing created successfully!', 'success')
                # Redirect to detail page of the new listing
                return redirect(url_for('listings.listing_detail', listing_id=listing.id))
    return render_template('listing_form.html', form=form, action="Create")

@listings_bp.route('/edit/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    """
    Edit an existing listing with ACID-like file handling using TEMP_DIR.
    - Only owner or admin can edit.
    - Deleted images are moved to temp before DB commit.
    - New images are stored in temp before DB commit.
    - If DB fails, all file changes are rolled back.
    - If DB succeeds, files are permanently changed.
    - On GET: show form pre-filled.
    - On POST: validate and update, handle image add/delete.
    - On error: stay on listing detail with flash message.
    """
    listing = Listing.query.get_or_404(listing_id)
    
    if current_user.id != listing.user_id and not current_user.is_admin:
        flash("You do not have permission to edit this listing.", "danger")
        return render_template("listing_detail.html", listing=listing)
    
    if not current_app.config['TEMP_DIR']:
        flash('Temp directory is not configured.', 'danger')
        return render_template("listing_detail.html", listing=listing)
    
    if not os.path.exists(current_app.config['TEMP_DIR']):
        flash('Temp directory does not exist. Please initialize the application.', 'danger')
        return render_template("listing_detail.html", listing=listing)
        
    types = Type.query.order_by(Type.name).all()
    form = ListingForm()
    form.type.choices = [(t.id, t.name) for t in types]
    categories = Category.query.filter_by(type_id=listing.type_id).all()
    form.category.choices = [(c.id, c.name) for c in categories]

    if request.method == 'POST':
        # Update choices for type/category dropdowns in form
        form.type.choices = [(t.id, t.name) for t in Type.query.order_by(Type.name)]
        form.category.choices = [
            (c.id, c.name) for c in Category.query.filter_by(type_id=form.type.data).order_by(Category.name)
        ]
        if form.validate_on_submit():
            listing.title = form.title.data
            listing.description = form.description.data
            listing.price = form.price.data or 0
            listing.type_id = form.type.data
            listing.category_id = form.category.data

            upload_dir = current_app.config['UPLOAD_DIR']
            temp_dir = current_app.config['TEMP_DIR']

            # For rollback
            moved_to_temp = []
            added_temp_paths = []
            added_files = []

            # --- Handle image deletions (move to temp, not delete) ---
            delete_image_ids = request.form.getlist('delete_images')
            if delete_image_ids:
                for img_id in delete_image_ids:
                    image = ListingImage.query.get(int(img_id))
                    if image and image in listing.images:
                        image_path = os.path.join(upload_dir, image.filename)
                        temp_path = os.path.join(temp_dir, image.filename)
                        try:
                            if os.path.exists(image_path):
                                shutil.move(image_path, temp_path)
                                moved_to_temp.append((image_path, temp_path))
                                db.session.delete(image)
                        except Exception as e:
                            flash(f'Error moving image {image.filename} to temp: {e}', 'warning')
            
            # --- Handle new image uploads (save to temp, not final location) ---
            if form.images.data:
                for file in form.images.data:
                    if file and file.filename:
                        ext = os.path.splitext(secure_filename(file.filename))[1]
                        unique_filename = f"{uuid.uuid4().hex}{ext}"
                        temp_path = os.path.join(temp_dir, unique_filename)
                        file.save(temp_path)
                        added_temp_paths.append((temp_path, unique_filename))
                        added_files.append(unique_filename)

            commit_success = False
            try:
                # Add new images to DB but don't move to final location yet
                for unique_filename in added_files:
                    image = ListingImage(filename=unique_filename, listing=listing)
                    db.session.add(image)
                db.session.commit()
                commit_success = True
            except Exception as e:
                db.session.rollback()
                # Restore deleted images from temp
                for orig_path, temp_path in moved_to_temp:
                    try:
                        if os.path.exists(temp_path):
                            shutil.move(temp_path, orig_path)
                    except Exception:
                        pass
                # Remove any temp-uploaded files
                for temp_path, _ in added_temp_paths:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception:
                        pass
                flash(f"Database error. Changes not saved. Files restored. ({e})", "danger")
                return render_template("listing_form.html", form=form, listing=listing, action="Save")
            
            # --- If commit succeeded: finalize file system changes ---
            if commit_success:
                # Permanently delete temp-ed images
                for _, temp_path in moved_to_temp:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception:
                        pass
                # Move new images from temp to upload dir
                for temp_path, unique_filename in added_temp_paths:
                    final_path = os.path.join(upload_dir, unique_filename)
                    try:
                        if os.path.exists(temp_path):
                            shutil.move(temp_path, final_path)
                    except Exception as e:
                        flash(f"Warning: Could not finalize upload for {unique_filename}: {e}", "warning")

                flash('Listing updated successfully!', 'success')
                return redirect(url_for('listings.listing_detail', listing_id=listing.id))
    else:
        # Only on GET: Pre-populate form fields from listing
        form.title.data = listing.title
        form.type.data = listing.type_id
        form.category.data = listing.category_id
        form.description.data = listing.description
        form.price.data = listing.price

    return render_template('listing_form.html', form=form, listing=listing, action="Save")

@listings_bp.route('/delete/<int:listing_id>', methods=['POST'])
@login_required
def delete_listing(listing_id):
    """
    Delete a single listing and its associated images using a temp directory for ACID-like safety.
    - Only owner or admin can delete.
    - Moves image files to a temp directory before DB operation.
    - On error: if DB commit fails, restores files from temp and stay on detail page with error flash.
    - On success: if DB commit succeeds, deletes files from temp and redirect to index.
    """
    listing = Listing.query.get_or_404(listing_id)
    
    if current_user.id != listing.user_id and not current_user.is_admin:
        flash("You do not have permission to delete this listing.", "danger")
        return render_template("listing_detail.html", listing=listing)

    if not current_app.config['TEMP_DIR']:
        flash('Temp directory is not configured.', 'danger')
        return render_template("listing_detail.html", listing=listing)
    
    if not os.path.exists(current_app.config['TEMP_DIR']):
        flash('Temp directory does not exist. Please initialize the application.', 'danger')
        return render_template("listing_detail.html", listing=listing)
        
    original_paths = []
    temp_paths = []

    # Move images to temp before DB commit
    for image in listing.images:
        orig = os.path.join(current_app.config['UPLOAD_DIR'], image.filename)
        temped = os.path.join(current_app.config['TEMP_DIR'], image.filename)
        try:
            if os.path.exists(orig):
                shutil.move(orig, temped)
                original_paths.append(orig)
                temp_paths.append(temped)
        except Exception as e:
            flash(f'Error moving image {image.filename} to temp: {e}', 'warning')

    try:
        db.session.delete(listing)
        db.session.commit()
    except Exception as e:
        # Restore files if DB fails
        for orig, temped in zip(original_paths, temp_paths):
            try:
                if os.path.exists(temped):
                    shutil.move(temped, orig)
            except Exception:
                pass
        db.session.rollback()
        flash(f'Database error. Listing was not deleted. Files restored. ({e})', 'danger')
        return render_template("listing_detail.html", listing=listing)

    # Permanently delete temped files after commit
    for temped in temp_paths:
        try:
            if os.path.exists(temped):
                os.remove(temped)
        except Exception:
            pass

    flash('Listing deleted successfully!', 'success')
    return redirect(url_for('listings.index'))