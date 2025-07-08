# Copyright (c) 2024 Fernando "ferabreu" Mees Abreu
# 
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Shared route utilities for the classifieds Flask app.

This module contains shared decorators and utility functions for use by multiple route Blueprints.
Currently, it provides the admin_required decorator for restricting access to admin users.
"""

from flask import flash, redirect, url_for
from flask_login import current_user
from functools import wraps

def admin_required(func):
    """
    Decorator to ensure the current user is an admin.

    - If the user is not authenticated or is not an admin,
      flashes an error message and redirects to the public listings index page.
    - Otherwise, allows access to the decorated view.

    Usage:
        @login_required
        @admin_required
        def admin_view():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for('listings.index'))
        return func(*args, **kwargs)
    return wrapper