# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot
at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

User and User Admin Blueprint routes and logic for Flask app.

This module contains user profile management and admin-level user management routes.
Admin-only routes are grouped under /admin/users and require the user to be an admin.
Self-service routes at /profile use @login_required only.
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from ..forms import UserEditForm
from ..models import Listing, User, db
from .decorators import admin_required
from .listings import _delete_listings_impl

users_bp = Blueprint("users", __name__)


# --------------------- USER ROUTES --------------------------


@users_bp.route("/profile")
@login_required
def profile():
    """User's own profile page (self-service)."""
    return render_template(
        "users/user_profile.html", user=current_user, page_title="Your profile"
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
        user.email = form.email.data.strip()  # type: ignore
        user.first_name = form.first_name.data.strip()  # type: ignore
        user.last_name = form.last_name.data.strip()  # type: ignore
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

    # Fetch users with listing counts in a single query using LEFT JOIN + GROUP BY.
    # This avoids the N+1 problem: instead of 1 query for users + 20 queries for counts,
    # we construct a subquery of listing counts grouped by user_id and join it to users.
    #
    # Using SQLAlchemy 2.0 select() API with subquery and outerjoin for aggregation.
    listing_count_subquery = (
        select(
            Listing.user_id,  # type: ignore
            func.count(Listing.id).label("listing_count"),
        )
        .group_by(Listing.user_id)
        .subquery()
    )

    # Join users with the subquery and fetch all columns including listing_count
    query = (
        select(
            User,
            func.coalesce(listing_count_subquery.c.listing_count, 0).label(
                "listing_count"
            ),
        )
        .outerjoin(
            listing_count_subquery, User.id == listing_count_subquery.c.user_id  # type: ignore
        )
        .order_by(sort_order)
    )

    # Use db.paginate for pagination (Flask-SQLAlchemy helper)
    pagination = db.paginate(query, page=page, per_page=20)  # type: ignore

    # Extract User objects and attach listing_count as an attribute for template
    users = []
    for row in pagination.items:
        # db.paginate() behavior with multi-column select is inconsistent:
        # - Sometimes returns tuple/Row: (User, listing_count)
        # - Sometimes returns User object with listing_count as attribute
        # Handle both cases to prevent TypeError during unpacking
        if isinstance(row, tuple):
            user, listing_count = row
        else:
            # Row is already the User object with listing_count attribute
            user = row
            listing_count = getattr(row, 'listing_count', 0)
        user.listing_count = listing_count
        users.append(user)
    pagination.items = users

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
    user = db.get_or_404(User, user_id)
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
    user = db.get_or_404(User, user_id)

    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        if form.is_admin.data is False:
            admins = db.session.execute(
                select(func.count(User.id)).where(User.is_admin)  # type: ignore
            ).scalar()
            if admins == 1 and user.is_admin:
                flash("Cannot remove the last administrator.", "danger")
                return redirect(url_for("users.admin_edit", user_id=user.id))
        user.email = form.email.data.strip()  # type: ignore
        user.first_name = form.first_name.data.strip()  # type: ignore
        user.last_name = form.last_name.data.strip()  # type: ignore
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
    """
    Allows admins to delete a user, except for the last admin user.
    Also deletes all listings owned by the user and their associated image files.
    """
    user = db.get_or_404(User, user_id)

    admins = db.session.execute(
        select(func.count(User.id)).where(User.is_admin)  # type: ignore
    ).scalar()
    if admins == 1 and user.is_admin:
        flash("Must have at least one admin user in the system.", "danger")
        return redirect(url_for("users.admin_list"))

    # Get all listings owned by the user with their images loaded
    listings = (
        db.session.execute(
            select(Listing)
            .where(Listing.user_id == user_id)
            .options(joinedload(Listing.images))  # type: ignore
        )
        .scalars()
        .unique()
        .all()
    )

    # Delete listings using the shared helper function
    success, error_message, listing_count = _delete_listings_impl(listings)

    if not success:
        flash(f"Error deleting user's listings: {error_message}", "danger")
        return redirect(url_for("users.admin_list"))

    # Delete user from database
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Database error. User was not deleted. ({e})", "danger")
        return redirect(url_for("users.admin_list"))

    # Provide appropriate feedback
    if listing_count > 0:
        flash(
            f"User deleted. Also deleted {listing_count} listing(s) "
            "owned by this user.",
            "success",
        )
    else:
        flash("User deleted.", "success")
    return redirect(url_for("users.admin_list"))
