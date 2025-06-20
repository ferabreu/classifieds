from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Type, Category, Item
from forms import TypeForm, CategoryForm, UserEditForm

admin_bp = Blueprint('admin', __name__)

def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for('items.index'))
        return func(*args, **kwargs)
    return wrapper

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    user_count = User.query.count()
    type_count = Type.query.count()
    category_count = Category.query.count()
    item_count = Item.query.count()
    return render_template('admin_dashboard.html', user_count=user_count, type_count=type_count, category_count=category_count, item_count=item_count)

# ---- USER ADMIN ----
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.order_by(User.email).all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        if user.email != "admin@classifieds.io" and form.is_admin.data is False:
            admins = User.query.filter_by(is_admin=True).count()
            if admins == 1 and user.is_admin:
                flash("Cannot remove the last administrator.", "danger")
                return redirect(url_for('admin.users'))
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_admin = form.is_admin.data
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('user_edit.html', form=form, user=user, admin_panel=True)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.email == "admin@classifieds.io":
        flash("Cannot delete the default admin.", "danger")
        return redirect(url_for('admin.users'))
    admins = User.query.filter_by(is_admin=True).count()
    if admins == 1 and user.is_admin:
        flash("Must have at least one admin.", "danger")
        return redirect(url_for('admin.users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin.users'))

# ---- TYPE ADMIN ----
@admin_bp.route('/types')
@login_required
@admin_required
def types():
    types = Type.query.order_by(Type.name).all()
    return render_template('admin_types.html', types=types)

@admin_bp.route('/types/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_type():
    form = TypeForm()
    if form.validate_on_submit():
        t = Type(name=form.name.data)
        db.session.add(t)
        db.session.commit()
        flash('Type created.', 'success')
        return redirect(url_for('admin.types'))
    return render_template('admin_type_form.html', form=form, action="Create")

@admin_bp.route('/types/edit/<int:type_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_type(type_id):
    t = Type.query.get_or_404(type_id)
    form = TypeForm(obj=t)
    if form.validate_on_submit():
        t.name = form.name.data
        db.session.commit()
        flash('Type updated.', 'success')
        return redirect(url_for('admin.types'))
    return render_template('admin_type_form.html', form=form, action="Edit", type_obj=t)

@admin_bp.route('/types/delete/<int:type_id>', methods=['POST'])
@login_required
@admin_required
def delete_type(type_id):
    t = Type.query.get_or_404(type_id)
    db.session.delete(t)
    db.session.commit()
    flash('Type deleted.', 'success')
    return redirect(url_for('admin.types'))

# ---- CATEGORY ADMIN ----
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.name).all()
    types = Type.query.order_by(Type.name).all()
    return render_template('admin_categories.html', categories=categories, types=types)

@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    form = CategoryForm()
    form.type_id.choices = [(t.id, t.name) for t in Type.query.order_by(Type.name)]
    if form.validate_on_submit():
        c = Category(name=form.name.data, type_id=form.type_id.data)
        db.session.add(c)
        db.session.commit()
        flash('Category created.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin_category_form.html', form=form, action="Create")

@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    c = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=c)
    form.type_id.choices = [(t.id, t.name) for t in Type.query.order_by(Type.name)]
    if form.validate_on_submit():
        c.name = form.name.data
        c.type_id = form.type_id.data
        db.session.commit()
        flash('Category updated.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin_category_form.html', form=form, action="Edit", category_obj=c)

@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    c = Category.query.get_or_404(category_id)
    db.session.delete(c)
    db.session.commit()
    flash('Category deleted.', 'success')
    return redirect(url_for('admin.categories'))

# ---- ITEM ADMIN ----
@admin_bp.route('/items')
@login_required
@admin_required
def items():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template('admin_items.html', items=items)

@admin_bp.route('/items/delete/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.', 'success')
    return redirect(url_for('admin.items'))