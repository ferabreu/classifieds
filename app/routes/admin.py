# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Admin Blueprint routes and logic for Flask app.

This module contains administrative views and utilities, including user, type, category, and listing management.
It ensures only admin users (with is_admin=True) can access these endpoints, and handles deletion of related images on the filesystem.
"""

import os
import shutil

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
from sqlalchemy.orm import joinedload

from ..forms import CategoryForm, TypeForm, UserEditForm
from ..models import Category, Listing, Type, User, db
from .utils import admin_required

# Blueprint for admin routes
admin_bp = Blueprint("admin", __name__)


# -------------------- DASHBOARD --------------------


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """
    Renders the admin dashboard with simple statistics on users, types, categories, and listings.
    """
    user_count = User.query.count()
    type_count = Type.query.count()
    category_count = Category.query.count()
    listing_count = Listing.query.count()
    return render_template(
        "admin/admin_dashboard.html",
        user_count=user_count,
        type_count=type_count,
        category_count=category_count,
        listing_count=listing_count,
        page_title="Admin dashboard",
    )


# -------------------- USER ADMIN --------------------


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    """
    Lists all users in the system, with sorting and pagination.
    """
    page = request.args.get("page", 1, type=int)
    sort = request.args.get("sort", "email")
    direction = request.args.get("direction", "asc")

    sort_column_map = {
        "email": User.email,
        "name": User.first_name,  # "Name" column sorts by first_name
        "is_admin": User.is_admin,
        "is_ldap_user": User.is_ldap_user,
        "id": User.id,
    }
    sort_column = sort_column_map.get(sort, User.email)
    sort_order = sort_column.asc() if direction == "asc" else sort_column.desc()

    pagination = User.query.order_by(sort_order).paginate(page=page, per_page=20)
    users = pagination.items
    return render_template(
        "admin/admin_users.html",
        users=users,
        pagination=pagination,
        sort=sort,
        direction=direction,
        page_title="Manage users",
    )


@admin_bp.route("/users/profile/<int:user_id>")
@login_required
@admin_required
def user_profile(user_id):
    """
    Displays a user's profile page for admin review.
    """
    user = User.query.get_or_404(user_id)
    return render_template(
        "users/user_profile.html", user=user, page_title="User profile"
    )


@admin_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
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
                return redirect(url_for("admin.edit_user", user_id=user.id))
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_admin = form.is_admin.data
        db.session.commit()
        flash("User updated.", "success")
        return redirect(url_for("admin.users"))
    return render_template(
        "users/user_edit.html",
        form=form,
        user=user,
        admin_panel=True,
        page_title="Edit user",
    )


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
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
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for("admin.users"))


# -------------------- TYPE ADMIN --------------------


@admin_bp.route("/types")
@login_required
@admin_required
def types():
    """
    Lists all listing types in the system.
    """
    types = Type.query.order_by(Type.name).all()
    return render_template(
        "admin/admin_types.html", types=types, page_title="Manage types"
    )


@admin_bp.route("/types/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_type():
    """
    Allows admins to create a new listing type.
    """
    form = TypeForm()
    if form.validate_on_submit():
        t = Type(name=form.name.data)
        db.session.add(t)
        db.session.commit()
        flash("Type created.", "success")
        return redirect(url_for("admin.types"))
    return render_template(
        "admin/admin_type_form.html",
        form=form,
        action="Create",
        page_title="Create type",
    )


@admin_bp.route("/types/edit/<int:type_id>", methods=["GET", "POST"])
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
        flash("Type updated.", "success")
        return redirect(url_for("admin.types"))
    return render_template(
        "admin/admin_type_form.html",
        form=form,
        action="Edit",
        type_obj=t,
        page_title="Edit type",
    )


@admin_bp.route("/types/delete/<int:type_id>", methods=["POST"])
@login_required
@admin_required
def delete_type(type_id):
    """
    Allows admins to delete a type only if it has no categories.
    """
    t = Type.query.get_or_404(type_id)
    if t.categories:  # If there are any categories, do not delete
        flash("You must delete all categories under this type first.", "danger")
        return redirect(url_for("admin.types"))
    db.session.delete(t)
    db.session.commit()
    flash("Type deleted.", "success")
    return redirect(url_for("admin.types"))


# -------------------- CATEGORY ADMIN --------------------


@admin_bp.route("/categories")
@login_required
@admin_required
def categories():
    """
    Lists all categories and types for admin management.
    """
    categories = Category.query.order_by(Category.name).all()
    types = Type.query.order_by(Type.name).all()
    return render_template(
        "admin/admin_categories.html",
        categories=categories,
        types=types,
        page_title="Manage categories",
    )


@admin_bp.route("/categories/new", methods=["GET", "POST"])
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
        flash("Category created.", "success")
        return redirect(url_for("admin.categories"))
    return render_template(
        "admin/admin_category_form.html",
        form=form,
        action="Create",
        page_title="Create category",
    )


@admin_bp.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
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
        flash("Category updated.", "success")
        return redirect(url_for("admin.categories"))
    return render_template(
        "admin/admin_category_form.html",
        form=form,
        action="Edit",
        category_obj=c,
        page_title="Edit category",
    )


@admin_bp.route("/categories/delete/<int:category_id>", methods=["POST"])
@login_required
@admin_required
def delete_category(category_id):
    """
    Allows admins to delete a category.
    """
    c = Category.query.get_or_404(category_id)
    db.session.delete(c)
    db.session.commit()
    flash("Category deleted.", "success")
    return redirect(url_for("admin.categories"))


# -------------------- LISTING ADMIN --------------------


@admin_bp.route("/listings")
@login_required
@admin_required
def listings():
    """
    Lists all listings (ordered by least recent) for admin management.
    """
    page = request.args.get("page", 1, type=int)

    sort = request.args.get("sort", "created_at")
    direction = request.args.get("direction", "desc")

    sort_column_map = {
        "title": Listing.title,
        "price": Listing.price,
        "type": Listing.type_id,
        "category": Listing.category_id,
        "user": Listing.user_id,
        "created_at": Listing.created_at,
    }
    sort_column = sort_column_map.get(sort, Listing.created_at)
    sort_order = sort_column.asc() if direction == "asc" else sort_column.desc()

    pagination = Listing.query.order_by(sort_order).paginate(page=page, per_page=20)
    listings = pagination.items

    return render_template(
        "admin/admin_listings.html",
        listings=listings,
        pagination=pagination,
        sort=sort,
        direction=direction,
        page_title="Manage listings",
    )


@admin_bp.route("/listings/delete/<int:listing_id>", methods=["POST"])
@login_required
@admin_required
def delete_listing(listing_id):
    """
    Deletes a single listing and its associated image files using a 'temp' strategy
    to approximate atomicity between database and filesystem operations.

    - Assumes the permanent temp directory exists (created at app init and referenced in config as TEMP_DIR).
    - Moves files to the temp before DB operation.
    - If DB commit fails, restores files from temp.
    - If DB commit succeeds, deletes files from temp.
    """
    listing = Listing.query.options(joinedload(Listing.images)).get_or_404(listing_id)
    original_paths = []
    temp_paths = []

    # Move all image files to the temp directory
    for image in listing.images:
        orig = os.path.join(current_app.config["UPLOAD_DIR"], image.filename)
        temped = os.path.join(current_app.config["TEMP_DIR"], image.filename)
        try:
            shutil.move(orig, temped)
            original_paths.append(orig)
            temp_paths.append(temped)
        except FileNotFoundError:
            # If file doesn't exist, just skip it
            pass

    try:
        # Attempt to delete the listing from the DB
        db.session.delete(listing)
        db.session.commit()
    except Exception as e:
        # If DB delete fails, move files back from temp
        for orig, temped in zip(original_paths, temp_paths):
            try:
                shutil.move(temped, orig)
            except Exception:
                pass  # Could log this if desired
        db.session.rollback()
        flash("Database error. Listing was not deleted. Files restored.", "danger")
        return redirect(url_for("admin.listings"))

    # If DB commit succeeded, permanently delete files from temp
    for temped in temp_paths:
        try:
            os.remove(temped)
        except Exception:
            pass  # Could log this if desired

    flash("Listing deleted.", "success")
    return redirect(url_for("admin.listings"))


@admin_bp.route("/listings/delete_selected", methods=["POST"])
@login_required
@admin_required
def delete_selected_listings():
    """
    Deletes multiple selected listings and all their associated image files using a 'temp' strategy
    to approximate atomicity between database and filesystem operations.

    - Moves files to the temp before DB operation.
    - If DB commit fails, restores files from temp.
    - If DB commit succeeds, deletes files from temp and also sweeps upload dir for any remaining orphans.
    """
    selected_ids = request.form.getlist("selected_listings")
    if not selected_ids:
        flash("No listings selected for deletion.", "warning")
        return redirect(url_for("admin.listings"))

    # Eagerly load images for all selected listings
    listings = (
        Listing.query.options(joinedload(Listing.images))
        .filter(Listing.id.in_(selected_ids))
        .all()
    )
    original_paths = []
    temp_paths = []
    all_image_filenames = set()

    # Move all related image files to temp and track all filenames
    for listing in listings:
        for image in listing.images:
            all_image_filenames.add(image.filename)
            orig = os.path.join(current_app.config["UPLOAD_DIR"], image.filename)
            temped = os.path.join(current_app.config["TEMP_DIR"], image.filename)
            try:
                shutil.move(orig, temped)
                original_paths.append(orig)
                temp_paths.append(temped)
            except FileNotFoundError:
                # If file doesn't exist, just skip it
                pass

    try:
        # Attempt to delete listings from the DB in a single transaction
        for listing in listings:
            db.session.delete(listing)
        db.session.commit()
    except Exception as e:
        # If DB delete fails, move files back from temp
        for orig, temped in zip(original_paths, temp_paths):
            try:
                shutil.move(temped, orig)
            except Exception:
                pass
        db.session.rollback()
        flash("Database error. Listings were not deleted. Files restored.", "danger")
        return redirect(url_for("admin.listings"))

    # If DB commit succeeded, permanently delete files from temp
    for temped in temp_paths:
        try:
            os.remove(temped)
        except Exception:
            pass  # Could log this if desired

    # Final sweep: delete any remaining files in upload dir associated with deleted listings
    for filename in all_image_filenames:
        path = os.path.join(current_app.config["UPLOAD_DIR"], filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass  # Could log this if desired

    flash(f"Deleted {len(listings)} listing(s).", "success")
    return redirect(url_for("admin.listings"))


# ----- End of admin.py -----
