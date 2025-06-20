from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Category, db

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/')
@login_required
def manage_categories():
    if not getattr(current_user, "is_admin", False):
        flash("Admin access required.", "danger")
        return redirect(url_for('items.index'))
    categories = Category.query.all()
    return render_template('category_manage.html', categories=categories)