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
Admin-only routes are grouped under /admin and require the user to be an admin.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..forms import UserEditForm
from ..models import User, db

users_bp = Blueprint("users", __name__)

# -------------------- USER PROFILE --------------------

@users_bp.route("/profile")
@login_required
def user_profile():
    user_id = request.args.get("user_id", type=int)
    if user_id and user_id != current_user.id:
        user = User.query.get_or_404(user_id)
        page_title = f"{user.first_name} {user.last_name}"
    else:
        user = current_user
        page_title = "Your profile"
    return render_template(
        "users/user_profile.html", user=user, page_title=page_title
    )


@users_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_user_profile():
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
        return redirect(url_for("users.user_profile"))
    return render_template(
        "users/user_edit.html",
        form=form,
        user=user,
        admin_panel=False,
        page_title="Edit profile",
    )
