# Copyright (c) 2024 Fernando "ferabreu" Mees Abreu
#
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Authentication and authorization routes for the classifieds Flask app.

Handles user login, logout, registration, password reset (with email or dev-mode token display),
and LDAP authentication if enabled. Uses Flask-Login for session management, Flask-Mail for
reset emails, and itsdangerous for password reset tokens.
"""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

from ..forms import ForgotPasswordForm, LoginForm, RegistrationForm, ResetPasswordForm
from ..ldap_auth import authenticate_with_ldap
from ..models import User, db

auth_bp = Blueprint("auth", __name__)


def generate_reset_token(email):
    """Generate a time-limited token for password reset using the user's email."""
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="reset-password")


def verify_reset_token(token, expiration=3600):
    """
    Verify a password reset token and retrieve the associated email.
    Returns None if the token is invalid or expired.
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = s.loads(token, salt="reset-password", max_age=expiration)
    except Exception:
        return None
    return email


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    User login route. Supports local and (optionally) LDAP authentication.
    Redirects an already authenticated user to the listings index.
    """
    if current_user.is_authenticated:
        return redirect(url_for("listings.index"))

    form = LoginForm()
    ldap_enabled = bool(
        current_app.config.get("LDAP_SERVER") and current_app.config.get("LDAP_DOMAIN")
    )

    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        # Try local authentication
        if user and user.password_hash and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("listings.index"))
        # Optionally, fall back to LDAP authentication
        if ldap_enabled and authenticate_with_ldap(email, password):
            if not user:
                # Automatically create a user account for LDAP logins if not found
                user = User(
                    email=email, first_name="LDAP", last_name="User", is_ldap_user=True
                )
                db.session.add(user)
                db.session.commit()
            login_user(user)
            flash("Logged in with LDAP.", "success")
            return redirect(url_for("listings.index"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html", form=form, ldap_enabled=ldap_enabled)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    User registration route. Only for non-logged-in users.
    Prevents duplicate registration by email.
    """
    if current_user.is_authenticated:
        return redirect(url_for("listings.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("register.html", form=form)
        user = User(
            email=email, first_name=form.first_name.data, last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """Logout route. Ends the user session and redirects to login."""
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    """
    Password reset request route.
    Sends a reset link by email (if configured), or flashes the link in dev mode.
    For LDAP users, disables password reset.
    """
    if current_user.is_authenticated:
        return redirect(url_for("listings.index"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and not user.is_ldap_user:
            token = generate_reset_token(user.email)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            if not current_app.config.get("MAIL_SERVER"):
                # Dev mode or no mail config: show reset link directly
                flash(f"[DEV] Password reset link: {reset_url}", "info")
            else:
                msg = Message(
                    subject="Password Reset Request",
                    recipients=[user.email],
                    body=f"Click the link to reset your password: {reset_url}",
                )
                from app import mail  # Import here to avoid circular import errors

                try:
                    mail.send(msg)
                    flash(
                        "If the account exists, a reset link has been sent to your email.",
                        "info",
                    )
                except Exception as e:
                    flash(f"Failed to send reset email. Error: {str(e)}", "danger")
        else:
            # Do not reveal whether the email exists or is LDAP user
            flash("If that account exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html", form=form)


@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    """
    Password reset route. Verifies the token, then allows password change.
    Redirects logged-in users away, and handles invalid/expired tokens safely.
    """
    if current_user.is_authenticated:
        return redirect(url_for("listings.index"))

    email = verify_reset_token(token)
    if not email:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.login"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(form.password.data)
            db.session.commit()
            flash("Password updated. Please log in.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("User not found.", "danger")
            return redirect(url_for("auth.login"))
    return render_template("reset_password.html", form=form)
