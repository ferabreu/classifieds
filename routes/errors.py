from flask import Blueprint, render_template

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template(
        "error.html",
        error_code=404,
        error_name="Page Not Found",
        error_description="The page or resource you requested could not be found."
    ), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    return render_template(
        "error.html",
        error_code=500,
        error_name="Internal Server Error",
        error_description="An unexpected error has occurred. Please try again later."
    ), 500

@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template(
        "error.html",
        error_code=403,
        error_name="Forbidden",
        error_description="You do not have permission to access this resource."
    ), 403