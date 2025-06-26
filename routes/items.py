# Created by GitHub Copilot for Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu)

from flask import Blueprint, current_app, jsonify, render_template, redirect, url_for, flash, request, g
from flask_login import login_required, current_user
from models import db, Item, ItemImage, Type, Category
from forms import ItemForm
from werkzeug.utils import secure_filename
import os, uuid, shutil

items_bp = Blueprint('items', __name__)

@items_bp.route('/')
def index():
    """Show all items, newest first."""
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template('index.html', items=items)

@items_bp.route('/type/<int:type_id>')
def by_type(type_id):
    """Show items filtered by type."""
    items = Item.query.filter_by(type_id=type_id).order_by(Item.created_at.desc()).all()
    selected_type = Type.query.get_or_404(type_id)
    return render_template('index.html', items=items, selected_type=selected_type)

@items_bp.route('/type/<int:type_id>/category/<int:category_id>')
def by_type_category(type_id, category_id):
    """Show items filtered by type and category."""
    items = Item.query.filter_by(type_id=type_id, category_id=category_id).order_by(Item.created_at.desc()).all()
    selected_type = Type.query.get_or_404(type_id)
    selected_category = Category.query.get_or_404(category_id)
    return render_template('index.html', items=items, selected_type=selected_type, selected_category=selected_category)

@items_bp.route('/item/<int:item_id>')
def item_detail(item_id):
    """Show details for a single item."""
    item = Item.query.get_or_404(item_id)
    return render_template('item_detail.html', item=item)

@items_bp.route('/categories_for_type/<int:type_id>')
@login_required
def categories_for_type(type_id):
    """
    Returns a JSON list of categories for a given type. Used for dynamic form population.
    """
    categories = Category.query.filter_by(type_id=type_id).order_by(Category.name).all()
    category_list = [{'id': c.id, 'name': c.name} for c in categories]
    return jsonify(category_list)

@items_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_item():
    """
    Create a new item with ACID-like file handling using TEMP_DIR.
    - On GET: show empty form.
    - On POST: validate and save item and images using atomic file/database logic.
    - Uploaded images are first saved to TEMP_DIR.
    - If DB commit succeeds, move images from TEMP_DIR to UPLOAD_DIR.
    - If DB commit fails, delete images from TEMP_DIR.
    - On success: redirect to detail page of the new item (not index).
    """
    form = ItemForm()
    
    if not current_app.config['TEMP_DIR']:
        flash('Temp directory is not configured.', 'danger')
        return render_template("item_form.html", form=form, action="Create")
    
    if not os.path.exists(current_app.config['TEMP_DIR']):
        flash('Temp directory does not exist. Please initialize the application.', 'danger')
        return render_template("item_form.html", form=form, action="Create")
        
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
            item = Item(
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
                # Add item and new images to DB but don't move to final location yet
                db.session.add(item)
                for unique_filename in added_files:
                    image = ItemImage(filename=unique_filename, item=item)
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
                flash(f"Database error. Item was not created. Uploaded files were discarded. ({e})", "danger")
                return render_template("item_form.html", form=form, action="Create")
            
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

                flash('Item created successfully!', 'success')
                # Redirect to detail page of the new item
                return redirect(url_for('items.item_detail', item_id=item.id))
    return render_template('item_form.html', form=form, action="Create")

@items_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    """
    Edit an existing item with ACID-like file handling using TEMP_DIR.
    - Only owner or admin can edit.
    - Deleted images are moved to temp before DB commit.
    - New images are stored in temp before DB commit.
    - If DB fails, all file changes are rolled back.
    - If DB succeeds, files are permanently changed.
    - On GET: show form pre-filled.
    - On POST: validate and update, handle image add/delete.
    - On error: stay on item detail with flash message.
    """
    item = Item.query.get_or_404(item_id)
    
    if current_user.id != item.user_id and not current_user.is_admin:
        flash("You do not have permission to edit this item.", "danger")
        return render_template("item_detail.html", item=item)
    
    if not current_app.config['TEMP_DIR']:
        flash('Temp directory is not configured.', 'danger')
        return render_template("item_detail.html", item=item)
    
    if not os.path.exists(current_app.config['TEMP_DIR']):
        flash('Temp directory does not exist. Please initialize the application.', 'danger')
        return render_template("item_detail.html", item=item)
        
    types = Type.query.order_by(Type.name).all()
    form = ItemForm()
    form.type.choices = [(t.id, t.name) for t in types]
    categories = Category.query.filter_by(type_id=item.type_id).all()
    form.category.choices = [(c.id, c.name) for c in categories]

    if request.method == 'POST':
        # Update choices for type/category dropdowns in form
        form.type.choices = [(t.id, t.name) for t in Type.query.order_by(Type.name)]
        form.category.choices = [
            (c.id, c.name) for c in Category.query.filter_by(type_id=form.type.data).order_by(Category.name)
        ]
        if form.validate_on_submit():
            item.title = form.title.data
            item.description = form.description.data
            item.price = form.price.data or 0
            item.type_id = form.type.data
            item.category_id = form.category.data

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
                    image = ItemImage.query.get(int(img_id))
                    if image and image in item.images:
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
                    image = ItemImage(filename=unique_filename, item=item)
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
                return render_template("item_form.html", form=form, item=item, action="Save")
            
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

                flash('Item updated successfully!', 'success')
                return redirect(url_for('items.item_detail', item_id=item.id))
    else:
        # Only on GET: Pre-populate form fields from item
        form.title.data = item.title
        form.type.data = item.type_id
        form.category.data = item.category_id
        form.description.data = item.description
        form.price.data = item.price

    return render_template('item_form.html', form=form, item=item, action="Save")

@items_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    """
    Delete a single item and its associated images using a temp directory for ACID-like safety.
    - Only owner or admin can delete.
    - Moves image files to a temp directory before DB operation.
    - On error: if DB commit fails, restores files from temp and stay on detail page with error flash.
    - On success: if DB commit succeeds, deletes files from temp and redirect to index.
    """
    item = Item.query.get_or_404(item_id)
    
    if current_user.id != item.user_id and not current_user.is_admin:
        flash("You do not have permission to delete this item.", "danger")
        return render_template("item_detail.html", item=item)

    if not current_app.config['TEMP_DIR']:
        flash('Temp directory is not configured.', 'danger')
        return render_template("item_detail.html", item=item)
    
    if not os.path.exists(current_app.config['TEMP_DIR']):
        flash('Temp directory does not exist. Please initialize the application.', 'danger')
        return render_template("item_detail.html", item=item)
        
    original_paths = []
    temp_paths = []

    # Move images to temp before DB commit
    for image in item.images:
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
        db.session.delete(item)
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
        flash(f'Database error. Item was not deleted. Files restored. ({e})', 'danger')
        return render_template("item_detail.html", item=item)

    # Permanently delete temped files after commit
    for temped in temp_paths:
        try:
            if os.path.exists(temped):
                os.remove(temped)
        except Exception:
            pass

    flash('Item deleted successfully!', 'success')
    return redirect(url_for('items.index'))