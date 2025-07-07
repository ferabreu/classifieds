from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from ..forms import UserEditForm
from ..models import db, User

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile')
@login_required
def my_profile():
    return render_template('user_profile.html', user=current_user)

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
    return render_template('user_edit.html', form=form, user=user, admin_panel=False)