# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot
at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Route decorators for the classifieds Flask app.

This module provides authorization decorators and permission helpers
for route protection.
"""

from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user, login_required


def admin_required(func):
    """
    Decorator to ensure the current user is authenticated and is an admin.

    This decorator implies @login_required - admin privileges require login.
    If the user is not authenticated or is not an admin, flashes an error
    message and redirects to the public listings index page.

    Usage:
        @admin_required
        def admin_view():
            ...

    Note: Do not stack with @login_required as it's already included.
    """

    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("listings.index"))
        return func(*args, **kwargs)

    return wrapper


def owner_or_admin_check(resource, user):
    """
    Helper function to check if a user is the owner of a resource or an admin.

    Args:
        resource: An object with a user_id attribute (e.g., Listing)
        user: The current user object (typically current_user)

    Returns:
        bool: True if user is the resource owner or an admin, False otherwise

    Usage:
        if not owner_or_admin_check(listing, current_user):
            flash("You do not have permission to edit this listing.", "danger")
            return redirect(url_for("listings.index"))
    """
    return resource.user_id == user.id or user.is_admin
