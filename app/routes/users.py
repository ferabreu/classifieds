# Copyright (c) 2024 Fernando "ferabreu" Mees Abreu
# 
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
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
from ..models import db, User

users_bp = Blueprint('users', __name__)

# -------------------- USER PROFILE (SELF) --------------------

@users_bp.route('/profile')
@login_required
def my_profile():
    return render_template('users/user_profile.html', user=current_user)

@users_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_my_profile():
    user = current_user
    form = UserEditForm(obj=user)
    # Never allow changing is_admin on self-edit in user routes
    if hasattr(form, 'is_admin'):
        delattr(form, 'is_admin')
    if form.validate_on_submit():
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('users.my_profile'))
    return render_template('users/user_edit.html', form=form, user=user, admin_panel=False)


