# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Categories Blueprint routes for Flask app.

This module contains all category-related routes including:
- Admin category management (list, create, edit, delete)
- AJAX/API endpoints for category data (breadcrumb, children)

All admin routes require admin privileges and use the @admin_required decorator.
API endpoints return JSON only and are used for AJAX calls from the frontend.
"""

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from ..forms import CategoryForm
from ..models import Category, Listing, db
from .decorators import admin_required

categories_bp = Blueprint("categories", __name__)

# -------------------- ADMIN ROUTES --------------------


@categories_bp.route("/admin/categories")
@admin_required
def admin_list():
    """
    Lists all categories for admin management.
    Shows hierarchy: parent and children.
    """
    categories = Category.query.order_by(Category.name).all()

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


@categories_bp.route("/admin/categories/new", methods=["GET", "POST"])
@admin_required
def admin_new():
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
        return redirect(url_for("categories.admin_list"))
    return render_template(
        "admin/admin_category_form.html",
        form=form,
        action="Create",
        page_title="Create category",
        exclude_ids=exclude_ids,
    )


@categories_bp.route("/admin/categories/edit/<int:category_id>", methods=["GET", "POST"])
@admin_required
def admin_edit(category_id):
    """
    Allows admins to edit an existing category.
    Updates url_name when the category name is altered.
    Prevents setting self or descendant as parent (cycle prevention).
    """
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    # compute ids to exclude (the category itself + all descendants) to avoid cycles
    exclude_ids = category.get_descendant_ids()

    # Populate parent_id choices (exclude self + descendants) so the hidden select has valid options
    all_cats = Category.query.order_by(Category.name).all()
    form.parent_id.choices = [("0", "- None -")] + [
        (str(cat.id), cat.get_full_path())
        for cat in all_cats
        if cat.id not in exclude_ids
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
            flash("Cannot set category itself or its descendant as parent.", "danger")
            return render_template(
                "admin/admin_category_form.html",
                form=form,
                action="Edit",
                category_obj=category,
                page_title="Edit category",
            )
        db.session.commit()
        flash("Category updated.", "success")
        return redirect(url_for("categories.admin_list"))
    return render_template(
        "admin/admin_category_form.html",
        form=form,
        action="Save",
        exclude_ids=exclude_ids,
        category=category,
    )


@categories_bp.route("/admin/categories/delete/<int:category_id>", methods=["POST"])
@admin_required
def admin_delete(category_id):
    """
    Allows admins to delete a category.
    Also deletes all descendant subcategories (cascade).
    Prevents deletion if category or descendants contain listings.
    """
    category = Category.query.get_or_404(category_id)

    # Build set of category ids to inspect: target + all descendants
    descendant_ids = set(category.get_descendant_ids() or [])
    ids_to_check = {category.id} | descendant_ids

    # Check for any listings in the category or any descendant category
    existing_listings = (
        Listing.query.with_entities(Listing.id)
        .filter(Listing.category_id.in_(ids_to_check))
        .first()
    )
    if existing_listings:
        flash(
            "Cannot delete category: it or one of its subcategories contains listings.",
            "danger",
        )
        return redirect(url_for("categories.admin_list"))

    db.session.delete(category)
    db.session.commit()
    flash("Category deleted.", "success")
    return redirect(url_for("categories.admin_list"))


# -------------------- API/AJAX ENDPOINTS --------------------


@categories_bp.route("/api/categories/children/<int:parent_id>")
@login_required
def api_children(parent_id):
    """
    Returns JSON array of direct children categories for a given parent.
    Used by AJAX calls for dynamic category dropdowns.

    Returns:
        JSON array of {id, name} objects for child categories.
    """
    children = Category.get_children(parent_id)
    data = [{"id": child.id, "name": child.name} for child in children]
    return jsonify(data)


@categories_bp.route("/api/categories/breadcrumb/<int:category_id>")
@login_required
def api_breadcrumb(category_id):
    """
    Returns JSON array representing the breadcrumb path for a category.
    Used by AJAX calls for pre-selecting dropdowns when editing.

    Returns:
        JSON array of category objects in breadcrumb path from root to target.
    """
    if category_id == 0:
        return jsonify([])  # No breadcrumb for root
    category = Category.query.get_or_404(category_id)
    return jsonify([c.to_dict() for c in category.breadcrumb])
