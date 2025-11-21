# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Admin Blueprint routes and logic for Flask app.

This module contains administrative views and utilities, including user, type, category, and listing management.
It ensures only admin users (with is_admin=True) can access these endpoints, and handles deletion of related images on the filesystem.
Category admin now supports hierarchical categories (parent-child).
"""

import os
import shutil

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from ..forms import CategoryForm, UserEditForm
from ..models import Category, Listing, User, db
from .utils import admin_required

admin_bp = Blueprint("admin", __name__)

# -------------------- DASHBOARD --------------------


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """Renders the admin dashboard with statistics on users, categories, listings."""
    user_count = User.query.count()
    category_count = Category.query.count()
    listing_count = Listing.query.count()
    return render_template(
        "admin/admin_dashboard.html",
        user_count=user_count,
        category_count=category_count,
        listing_count=listing_count,
        page_title="Admin dashboard",
    )


# -------------------- USER ADMIN --------------------


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    """Lists all users in the system, with sorting and pagination."""
    page = request.args.get("page", 1, type=int)
    sort = request.args.get("sort", "email")
    direction = request.args.get("direction", "asc")

    sort_column_map = {
        "email": User.email,
        "name": User.first_name,
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
    """Displays a user's profile page for admin review."""
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
    """Allows admins to delete a user, except for the last admin user."""
    user = User.query.get_or_404(user_id)
    admins = User.query.filter_by(is_admin=True).count()
    if admins == 1 and user.is_admin:
        flash("Must have at least one admin user in the system.", "danger")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for("admin.users"))


# -------------------- CATEGORY ADMIN --------------------


@admin_bp.route("/categories")
@login_required
@admin_required
def categories():
    """
    Lists all categories for admin management.
    Shows hierarchy: parent and children.
    """
    categories = Category.query.order_by(Category.name).all()
    from app.forms import CategoryForm

    forms = {}
    for c in categories:
        form = CategoryForm(obj=c)
        # Set parent_id choices, exclude self
        form.parent_id.choices = [("0", "- None -")] + [
            (str(cat.id), cat.get_full_path()) for cat in categories if cat.id != c.id
        ]  # type: ignore
        # Set the current parent_id value
        form.parent_id.data = str(c.parent_id) if c.parent_id else "0"
        forms[c.id] = form
    return render_template(
        "admin/admin_categories.html",
        categories=categories,
        forms=forms,
        page_title="Manage categories",
    )


@admin_bp.route("/categories/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_category():
    """
    Allows admins to create a new category.
    Assigns a parent category if desired (for hierarchy).
    """
    form = CategoryForm()
    # Populate parent_id choices: show all categories except self (no actual self yet)
    form.parent_id.choices = [("0", "- None -")] + [
        (str(cat.id), cat.get_full_path())
        for cat in Category.query.order_by(Category.name).all()
    ]  # type: ignore
    exclude_ids = []  # no category to exclude when creating new
    if form.validate_on_submit():
        name = form.name.data
        assert isinstance(name, str)
        parent_id = int(form.parent_id.data) if form.parent_id.data != "0" else None
        c = Category(name=name, parent_id=parent_id)
        db.session.add(c)
        db.session.commit()
        flash("Category created.", "success")
        return redirect(url_for("admin.categories"))
    return render_template(
        "admin/admin_category_form.html",
        form=form,
        action="Create",
        page_title="Create category",
        exclude_ids=exclude_ids,
    )


@admin_bp.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    # compute ids to exclude (the category itself + all descendants) to avoid cycles
    exclude_ids = category.get_descendant_ids()

    # Populate parent_id choices (exclude self + descendants) so the hidden select has valid options
    all_cats = Category.query.order_by(Category.name).all()
    form.parent_id.choices = [("0", "- None -")] + [
        (str(cat.id), cat.get_full_path()) for cat in all_cats if cat.id not in exclude_ids
    ]  # type: ignore

    if request.method == "GET":
        # Set the current parent value as a string to match SelectField choice values
        form.parent_id.data = str(category.parent_id) if category.parent_id else "0"

    if form.validate_on_submit():
        category.name = form.name.data
        category.parent_id = (
            int(form.parent_id.data) if form.parent_id.data != "0" else None
        )
        # Prevent setting self or descendant as parent
        if category.parent_id is not None and category.parent_id in exclude_ids:
            flash(
                "Cannot set category itself or its descendant as parent.", "danger"
            )
            return render_template(
                "admin/admin_category_form.html",
                form=form,
                action="Edit",
                category_obj=category,
                page_title="Edit category",
            )
        db.session.commit()
        flash("Category updated.", "success")
        return redirect(url_for("admin.categories"))
    return render_template(
        "admin/admin_category_form.html",
        form=form,
        action="Save",
        exclude_ids=exclude_ids,
        category=category,
    )


@admin_bp.route("/categories/delete/<int:category_id>", methods=["POST"])
@login_required
@admin_required
def delete_category(category_id):
    """
    Allows admins to delete a category.
    Also deletes all descendant subcategories (cascade).
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
    """
    listing = Listing.query.options(joinedload(Listing.images)).get_or_404(listing_id)  # type: ignore
    original_paths = []
    temp_paths = []

    for image in listing.images:
        orig = os.path.join(current_app.config["UPLOAD_DIR"], image.filename)
        temped = os.path.join(current_app.config["TEMP_DIR"], image.filename)
        try:
            shutil.move(orig, temped)
            original_paths.append(orig)
            temp_paths.append(temped)
        except FileNotFoundError:
            pass

    try:
        db.session.delete(listing)
        db.session.commit()
    except Exception:
        for orig, temped in zip(original_paths, temp_paths):
            try:
                shutil.move(temped, orig)
            except Exception:
                pass
        db.session.rollback()
        flash("Database error. Listing was not deleted. Files restored.", "danger")
        return redirect(url_for("admin.listings"))

    for temped in temp_paths:
        try:
            os.remove(temped)
        except Exception:
            pass

    flash("Listing deleted.", "success")
    return redirect(url_for("admin.listings"))


@admin_bp.route("/listings/delete_selected", methods=["POST"])
@login_required
@admin_required
def delete_selected_listings():
    """
    Deletes multiple selected listings and all their associated image files using a 'temp' strategy.
    """
    selected_ids = request.form.getlist("selected_listings")
    if not selected_ids:
        flash("No listings selected for deletion.", "warning")
        return redirect(url_for("admin.listings"))

    listings = (
        Listing.query.options(joinedload(Listing.images))  # type: ignore
        .filter(Listing.id.in_(selected_ids))
        .all()
    )
    original_paths = []
    temp_paths = []
    all_image_filenames = set()

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
                pass

    try:
        for listing in listings:
            db.session.delete(listing)
        db.session.commit()
    except Exception:
        for orig, temped in zip(original_paths, temp_paths):
            try:
                shutil.move(temped, orig)
            except Exception:
                pass
        db.session.rollback()
        flash("Database error. Listings were not deleted. Files restored.", "danger")
        return redirect(url_for("admin.listings"))

    for temped in temp_paths:
        try:
            os.remove(temped)
        except Exception:
            pass

    for filename in all_image_filenames:
        path = os.path.join(current_app.config["UPLOAD_DIR"], filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    flash(f"Deleted {len(listings)} listing(s).", "success")
    return redirect(url_for("admin.listings"))
