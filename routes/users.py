from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User
from forms import UserEditForm

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_profile.html', user=user)

@users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.id != user.id and not current_user.is_admin:
        flash("You do not have permission to edit this user.", "danger")
        return redirect(url_for('users.profile', user_id=user.id))
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('users.profile', user_id=user.id))
    return render_template('user_edit.html', form=form, user=user, admin_panel=False)