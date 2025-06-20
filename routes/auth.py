from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from models import db, User
from forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from ldap_auth import authenticate_with_ldap
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message

auth_bp = Blueprint('auth', __name__)

def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='reset-password')

def verify_reset_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='reset-password', max_age=expiration)
    except Exception:
        return None
    return email

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('items.index'))
    form = LoginForm()
    ldap_enabled = bool(current_app.config.get("LDAP_SERVER") and current_app.config.get("LDAP_DOMAIN"))
    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and user.password_hash and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for('items.index'))
        if ldap_enabled and authenticate_with_ldap(email, password):
            if not user:
                user = User(
                    email=email,
                    first_name='LDAP',
                    last_name='User',
                    is_ldap_user=True
                )
                db.session.add(user)
                db.session.commit()
            login_user(user)
            flash("Logged in with LDAP.", "success")
            return redirect(url_for('items.index'))
        flash("Invalid credentials.", "danger")
    return render_template('login.html', form=form, ldap_enabled=ldap_enabled)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('items.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template('register.html', form=form)
        user = User(
            email=email,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('items.index'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and not user.is_ldap_user:
            token = generate_reset_token(user.email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            # Send email
            msg = Message(
                subject="Password Reset Request",
                recipients=[user.email],
                body=f"Click the link to reset your password: {reset_url}"
            )
            from app import mail
            try:
                mail.send(msg)
                flash("If the account exists, a reset link has been sent to your email.", "info")
            except Exception as e:
                flash(f"Failed to send reset email. Error: {str(e)}", "danger")
        else:
            flash("If that account exists, a reset link has been sent.", "info")
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html', form=form)

@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('items.index'))
    email = verify_reset_token(token)
    if not email:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for('auth.login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(form.password.data)
            db.session.commit()
            flash("Password updated. Please log in.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("User not found.", "danger")
            return redirect(url_for('auth.login'))
    return render_template('reset_password.html', form=form)