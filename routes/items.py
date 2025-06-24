# Created by GitHub Copilot for Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu)

from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request, g
from flask_login import login_required, current_user
from models import db, Item, ItemImage, Type, Category
from forms import ItemForm
from werkzeug.utils import secure_filename
import os, uuid

items_bp = Blueprint('items', __name__)
UPLOAD_FOLDER = 'static/uploads'

@items_bp.route('/')
def index():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template('index.html', items=items)

@items_bp.route('/type/<int:type_id>')
def by_type(type_id):
    items = Item.query.filter_by(type_id=type_id).order_by(Item.created_at.desc()).all()
    selected_type = Type.query.get_or_404(type_id)
    return render_template('index.html', items=items, selected_type=selected_type)

@items_bp.route('/type/<int:type_id>/category/<int:category_id>')
def by_type_category(type_id, category_id):
    items = Item.query.filter_by(type_id=type_id, category_id=category_id).order_by(Item.created_at.desc()).all()
    selected_type = Type.query.get_or_404(type_id)
    selected_category = Category.query.get_or_404(category_id)
    return render_template('index.html', items=items, selected_type=selected_type, selected_category=selected_category)

@items_bp.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item_detail.html', item=item)

@items_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_item():
    types = Type.query.order_by(Type.name).all()
    form = ItemForm()
    form.type.choices = [(t.id, t.name) for t in types]
    # Default to first type's categories
    categories = Category.query.filter_by(type_id=types[0].id).all() if types else []
    form.category.choices = [(c.id, c.name) for c in categories]
    if request.method == 'POST':
        form.type.choices = [(t.id, t.name) for t in Type.query.order_by(Type.name)]
        form.category.choices = [(c.id, c.name) for c in Category.query.filter_by(type_id=form.type.data).order_by(Category.name)]
        if form.validate_on_submit():
            item = Item(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data or 0,
                user_id=current_user.id,
                type_id=form.type.data,
                category_id=form.category.data
            )
            if form.images.data:
                for file in form.images.data:
                    if file and file.filename:  # Make sure the file exists
                        # Get the file extension
                        ext = os.path.splitext(secure_filename(file.filename))[1]
                        # Generate a unique filename with UUID
                        unique_filename = f"{uuid.uuid4().hex}{ext}"
                        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                        # Create an ItemImage record or append to item.images as appropriate
                        image = ItemImage(filename=unique_filename, item=item)
                        db.session.add(image)
            db.session.add(item)
            db.session.commit()
            flash('Item created successfully!', 'success')
            return redirect(url_for('items.index'))
    return render_template('item_form.html', form=form, action="Create")

@items_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if current_user.id != item.user_id and not current_user.is_admin:
        flash("You do not have permission to edit this item.", "danger")
        return redirect(url_for('items.index'))
    
    types = Type.query.order_by(Type.name).all()
    form = ItemForm()
    form.type.choices = [(t.id, t.name) for t in types]
    categories = Category.query.filter_by(type_id=item.type_id).all()
    form.category.choices = [(c.id, c.name) for c in categories]

    if request.method == 'POST':
        # Update choices in case user changed type in the form
        form.type.choices = [(t.id, t.name) for t in Type.query.order_by(Type.name)]
        form.category.choices = [
            (c.id, c.name) for c in Category.query.filter_by(type_id=form.type.data).order_by(Category.name)
        ]
        if form.validate_on_submit():
            item.title = form.title.data
            item.description = form.description.data
            item.price = form.price.data or 0
            item.type_id = form.type.data
            item.category_id = form.category.data

            # Handle image deletions
            delete_image_ids = request.form.getlist('delete_images')
            if delete_image_ids:
                for img_id in delete_image_ids:
                    image = ItemImage.query.get(int(img_id))
                    if image and image in item.images:
                        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                        db.session.delete(image)

            # Handle new image uploads
            if form.images.data:
                for file in form.images.data:
                    if file and file.filename:
                        ext = os.path.splitext(secure_filename(file.filename))[1]
                        unique_filename = f"{uuid.uuid4().hex}{ext}"
                        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                        image = ItemImage(filename=unique_filename, item=item)
                        db.session.add(image)

            db.session.commit()
            flash('Item updated successfully!', 'success')
            return redirect(url_for('items.item_detail', item_id=item.id))
    else:
        # Only on GET: Pre-populate form fields from item
        form.title.data = item.title
        form.type.data = item.type_id
        form.category.data = item.category_id
        form.description.data = item.description
        form.price.data = item.price

    return render_template('item_form.html', form=form, item=item, action="Save")

@items_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if current_user.id != item.user_id and not current_user.is_admin:
        flash("You do not have permission to delete this item.", "danger")
        return redirect(url_for('items.index'))

    # Optional: delete image files from disk
    for image in item.images:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('items.index'))