"""
admin.py - Admin Blueprint routes and logic for Flask app.

NOTE: This code was written and annotated by GitHub Copilot at the request of ferabreu.

This module contains administrative views and utilities, including user, type, category, and item management.
It ensures only admin users (with is_admin=True) can access these endpoints, and handles deletion of related images on the filesystem.
"""

from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Type, Category, Item
from forms import TypeForm, CategoryForm, UserEditForm
from sqlalchemy.orm import joinedload
import os, shutil

# Blueprint for admin routes
admin_bp = Blueprint('admin', __name__)

def admin_required(func):
    """
    Decorator to ensure the current user is an admin.
    - Redirects to the public items index page with an error flash if not.
    """
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for('items.index'))
        return func(*args, **kwargs)
    return wrapper

# -------------------- DASHBOARD --------------------

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """
    Renders the admin dashboard with simple statistics on users, types, categories, and items.
    """
    user_count = User.query.count()
    type_count = Type.query.count()
    category_count = Category.query.count()
    item_count = Item.query.count()
    return render_template(
        'admin_dashboard.html',
        user_count=user_count,
        type_count=type_count,
        category_count=category_count,
        item_count=item_count
    )

# -------------------- USER ADMIN --------------------

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """
    Lists all users in the system, ordered by email.
    """
    users = User.query.order_by(User.email).all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/users/profile/<int:user_id>')
@login_required
@admin_required
def user_profile(user_id):
    """
    Displays a user's profile page for admin review.
    """
    user = User.query.get_or_404(user_id)
    return render_template('user_profile.html', user=user)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """
    Allows admins to edit user details, including admin status.
    Prevents demoting the last admin in the system.
    """
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        # Prevent removing the last admin
        if form.is_admin.data is False:
            admins = User.query.filter_by(is_admin=True).count()
            if admins == 1 and user.is_admin:
                flash("Cannot remove the last administrator.", "danger")
                return redirect(url_for('admin.edit_user', user_id=user.id))
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_admin = form.is_admin.data
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('user_edit.html', form=form, user=user, admin_panel=True)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """
    Allows admins to delete a user, except for the last admin user.
    """
    user = User.query.get_or_404(user_id)
    admins = User.query.filter_by(is_admin=True).count()
    # Prevent deletion if this is the last admin
    if admins == 1 and user.is_admin:
        flash("Must have at least one admin user in the system.", "danger")
        return redirect(url_for('admin.users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin.users'))

# -------------------- TYPE ADMIN --------------------

@admin_bp.route('/types')
@login_required
@admin_required
def types():
    """
    Lists all item types in the system.
    """
    types = Type.query.order_by(Type.name).all()
    return render_template('admin_types.html', types=types)

@admin_bp.route('/types/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_type():
    """
    Allows admins to create a new item type.
    """
    form = TypeForm()
    if form.validate_on_submit():
        t = Type(name=form.name.data)
        db.session.add(t)
        db.session.commit()
        flash('Type created.', 'success')
        return redirect(url_for('admin.types'))
    return render_template('admin_type_form.html', form=form, action="Create")

@admin_bp.route('/types/edit/<int:type_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_type(type_id):
    """
    Allows admins to edit an existing type's name.
    """
    t = Type.query.get_or_404(type_id)
    form = TypeForm(obj=t)
    if form.validate_on_submit():
        t.name = form.name.data
        db.session.commit()
        flash('Type updated.', 'success')
        return redirect(url_for('admin.types'))
    return render_template('admin_type_form.html', form=form, action="Edit", type_obj=t)

@admin_bp.route('/types/delete/<int:type_id>', methods=['POST'])
@login_required
@admin_required
def delete_type(type_id):
    """
    Allows admins to delete a type.
    """
    t = Type.query.get_or_404(type_id)
    db.session.delete(t)
    db.session.commit()
    flash('Type deleted.', 'success')
    return redirect(url_for('admin.types'))

# -------------------- CATEGORY ADMIN --------------------

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """
    Lists all categories and types for admin management.
    """
    categories = Category.query.order_by(Category.name).all()
    types = Type.query.order_by(Type.name).all()
    return render_template('admin_categories.html', categories=categories, types=types)

@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    """
    Allows admins to create a new category and assign it to a type.
    """
    form = CategoryForm()
    form.type_id.choices = [(t.id, t.name) for t in Type.query.order_by(Type.name)]
    if form.validate_on_submit():
        c = Category(name=form.name.data, type_id=form.type_id.data)
        db.session.add(c)
        db.session.commit()
        flash('Category created.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin_category_form.html', form=form, action="Create")

@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    """
    Allows admins to edit a category's name and type assignment.
    """
    c = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=c)
    form.type_id.choices = [(t.id, t.name) for t in Type.query.order_by(Type.name)]
    if form.validate_on_submit():
        c.name = form.name.data
        c.type_id = form.type_id.data
        db.session.commit()
        flash('Category updated.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin_category_form.html', form=form, action="Edit", category_obj=c)

@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """
    Allows admins to delete a category.
    """
    c = Category.query.get_or_404(category_id)
    db.session.delete(c)
    db.session.commit()
    flash('Category deleted.', 'success')
    return redirect(url_for('admin.categories'))

# -------------------- ITEM ADMIN --------------------

@admin_bp.route('/items')
@login_required
@admin_required
def items():
    """
    Lists all items (ordered by most recent) for admin management.
    """
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template('admin_items.html', items=items)

@admin_bp.route('/items/delete/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def delete_item(item_id):
    """
    Deletes a single item and its associated image files using a 'trash' strategy
    to approximate atomicity between database and filesystem operations.

    - Assumes the permanent trash directory exists (created at app init and referenced in config as TRASH_DIR).
    - Moves files to the trash before DB operation.
    - If DB commit fails, restores files from trash.
    - If DB commit succeeds, deletes files from trash.
    """
    trash_dir = current_app.config['TRASH_DIR']
    item = Item.query.options(joinedload(Item.images)).get_or_404(item_id)
    original_paths = []
    trash_paths = []

    # Move all image files to the permanent trash
    for image in item.images:
        orig = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename)
        trashed = os.path.join(trash_dir, image.filename)
        try:
            shutil.move(orig, trashed)
            original_paths.append(orig)
            trash_paths.append(trashed)
        except FileNotFoundError:
            # If file doesn't exist, just skip it
            pass

    try:
        # Attempt to delete the item from the DB
        db.session.delete(item)
        db.session.commit()
    except Exception as e:
        # If DB delete fails, move files back from trash
        for orig, trashed in zip(original_paths, trash_paths):
            try:
                shutil.move(trashed, orig)
            except Exception:
                pass  # Could log this if desired
        db.session.rollback()
        flash('Database error. Item was not deleted. Files restored.', 'danger')
        return redirect(url_for('admin.items'))

    # If DB commit succeeded, permanently delete files from trash
    for trashed in trash_paths:
        try:
            os.remove(trashed)
        except Exception:
            pass  # Could log this if desired

    flash('Item deleted.', 'success')
    return redirect(url_for('admin.items'))

@admin_bp.route('/items/delete_selected', methods=['POST'])
@login_required
@admin_required
def delete_selected_items():
    """
    Deletes multiple selected items and all their associated image files using a 'trash' strategy
    to approximate atomicity between database and filesystem operations.

    - Assumes the permanent trash directory exists (created at app init and referenced in config as TRASH_DIR).
    - Moves files to the trash before DB operation.
    - If DB commit fails, restores files from trash.
    - If DB commit succeeds, deletes files from trash.
    """
    selected_ids = request.form.getlist('selected_items')
    if not selected_ids:
        flash("No items selected for deletion.", "warning")
        return redirect(url_for('admin.items'))

    trash_dir = current_app.config['TRASH_DIR']

    # Eagerly load images for all selected items
    items = Item.query.options(joinedload(Item.images)).filter(Item.id.in_(selected_ids)).all()
    original_paths = []
    trash_paths = []

    # Move all related image files to trash
    for item in items:
        for image in item.images:
            orig = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename)
            trashed = os.path.join(trash_dir, image.filename)
            try:
                shutil.move(orig, trashed)
                original_paths.append(orig)
                trash_paths.append(trashed)
            except FileNotFoundError:
                # If file doesn't exist, just skip it
                pass

    try:
        # Attempt to delete items from the DB in a single transaction
        for item in items:
            db.session.delete(item)
        db.session.commit()
    except Exception as e:
        # If DB delete fails, move files back from trash
        for orig, trashed in zip(original_paths, trash_paths):
            try:
                shutil.move(trashed, orig)
            except Exception:
                pass  # Could log this if desired
        db.session.rollback()
        flash('Database error. Items were not deleted. Files restored.', 'danger')
        return redirect(url_for('admin.items'))

    # If DB commit succeeded, permanently delete files from trash
    for trashed in trash_paths:
        try:
            os.remove(trashed)
        except Exception:
            pass  # Could log this if desired

    flash(f"Deleted {len(items)} item(s).", "success")
    return redirect(url_for('admin.items'))

# ----- End of admin.py -----