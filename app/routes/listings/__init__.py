# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
Listings Blueprint package for Flask app.

This package contains all listing-related routes and helper functions including:
- Public listing views (index, category browsing, listing details)
- User listing management (create, edit, delete listings with images)
- Admin listing management (bulk operations, moderation)
- Image upload/thumbnail generation with atomic temp->commit->move pattern
- Category-based filtering and showcase displays
"""

from flask import Blueprint

listings_bp = Blueprint("listings", __name__)

# Import routes to register them with the blueprint
# noqa comments suppress import order warnings since routes need the blueprint
from . import routes  # noqa: F401, E402
