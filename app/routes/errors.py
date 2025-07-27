# Copyright (c) 2024 Fernando "ferabreu" Mees Abreu
#
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Error handler routes for the classifieds Flask app.

Defines custom responses for common HTTP errors (404, 500, 403), rendering a user-friendly error page
with appropriate status code and descriptive messages.
"""

from flask import Blueprint, render_template

errors_bp = Blueprint("errors", __name__)


@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """
    Handler for 404 Not Found errors.
    Renders a custom error page when a page or resource is missing.
    """
    return (
        render_template(
            "error.html",
            error_code=404,
            error_name="Page Not Found",
            error_description="The page or resource you requested could not be found.",
        ),
        404,
    )


@errors_bp.app_errorhandler(500)
def internal_error(error):
    """
    Handler for 500 Internal Server Error.
    Renders a custom error page when an unexpected server error occurs.
    """
    return (
        render_template(
            "error.html",
            error_code=500,
            error_name="Internal Server Error",
            error_description="An unexpected error has occurred. Please try again later.",
        ),
        500,
    )


@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    """
    Handler for 403 Forbidden errors.
    Renders a custom error page when access to a resource is denied.
    """
    return (
        render_template(
            "error.html",
            error_code=403,
            error_name="Forbidden",
            error_description="You do not have permission to access this resource.",
        ),
        403,
    )
