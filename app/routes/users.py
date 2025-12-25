# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

User and User Admin Blueprint routes and logic for Flask app.

This module contains user profile management and admin-level user management routes.
Admin-only routes are grouped under /admin/users and require the user to be an admin.
Self-service routes at /profile use @login_required only.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..forms import UserEditForm
from ..models import User, db
from .decorators import admin_required

users_bp = Blueprint("users", __name__)

# -------------------- USER SELF-SERVICE --------------------

@users_bp.route("/profile")
@login_required
def profile():
    """User's own profile page (self-service)."""
    return render_template(
        "users/user_profile.html",
        user=current_user,
        page_title="Your profile"
    )


@users_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """User self-service profile edit. Cannot change admin status."""
    user = current_user
    form = UserEditForm(obj=user)

    # Never allow changing is_admin on self-edit in user routes
    if hasattr(form, "is_admin"):
        delattr(form, "is_admin")
    if form.validate_on_submit():
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("users.profile"))
    return render_template(
        "users/user_form.html",
        form=form,
        user=user,
        admin_panel=False,
        page_title="Edit profile",
    )


# -------------------- ADMIN USER MANAGEMENT --------------------

@users_bp.route("/admin/users")
@admin_required
def admin_list():
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


@users_bp.route("/admin/users/profile/<int:user_id>")
@admin_required
def admin_profile(user_id):
    """Displays a user's profile page for admin review."""
    user = User.query.get_or_404(user_id)
    return render_template(
        "users/user_profile.html", user=user, page_title="User profile"
    )


@users_bp.route("/admin/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def admin_edit(user_id):
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
                return redirect(url_for("users.admin_edit", user_id=user.id))
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_admin = form.is_admin.data
        db.session.commit()
        flash("User updated.", "success")
        return redirect(url_for("users.admin_list"))
    return render_template(
        "users/user_form.html",
        form=form,
        user=user,
        admin_panel=True,
        page_title="Edit user",
    )


@users_bp.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def admin_delete(user_id):
    """Allows admins to delete a user, except for the last admin user."""
    user = User.query.get_or_404(user_id)
    admins = User.query.filter_by(is_admin=True).count()
    if admins == 1 and user.is_admin:
        flash("Must have at least one admin user in the system.", "danger")
        return redirect(url_for("users.admin_list"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for("users.admin_list"))


@users_bp.route("/admin/users/delete_selected", methods=["POST"])
@admin_required
def delete_selected_users():
    """
    Deletes multiple selected users.
    Prevents deletion if it would result in no admin users remaining.
    """
    selected_ids = request.form.getlist("selected_users")
    if not selected_ids:
        flash("No users selected for deletion.", "warning")
        return redirect(url_for("users.admin_list"))

    # Convert to integers
    selected_ids = [int(user_id) for user_id in selected_ids]

    # Check if all admin users are being deleted
    admin_count = User.query.filter_by(is_admin=True).count()
    admin_in_selection = User.query.filter(
        User.id.in_(selected_ids), User.is_admin.is_(True)
    ).count()

    if admin_in_selection == admin_count:
        flash(
            "Cannot delete all administrators. At least one admin must remain.",
            "danger",
        )
        return redirect(url_for("users.admin_list"))

    users_to_delete = User.query.filter(User.id.in_(selected_ids)).all()

    try:
        for user in users_to_delete:
            db.session.delete(user)
        db.session.commit()
        flash(f"Deleted {len(users_to_delete)} user(s).", "success")
    except Exception:
        db.session.rollback()
        flash("Database error. Users were not deleted.", "danger")
        return redirect(url_for("users.admin_list"))

    return redirect(url_for("users.admin_list"))
