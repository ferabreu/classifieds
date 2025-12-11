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

from flask import (
    Blueprint,
    render_template,
)

from ..models import Category, Listing, User
from .decorators import admin_required

admin_bp = Blueprint("admin", __name__)

# -------------------- DASHBOARD --------------------


@admin_bp.route("/dashboard")
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
