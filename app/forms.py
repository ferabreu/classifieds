# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot
at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

WTForms form definitions for user management, listings, and categories.

Includes custom validation logic for listing details and user data.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import (
    BooleanField,
    FloatField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

from .models import RESERVED_CATEGORY_NAMES, Category, generate_url_name


class RegistrationForm(FlaskForm):
    """
    Form for user registration.
    """

    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=64)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    """
    Form for user login.
    """

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class ForgotPasswordForm(FlaskForm):
    """
    Form for requesting password reset.
    """

    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send reset link")


class ResetPasswordForm(FlaskForm):
    """
    Form for resetting password.
    """

    password = PasswordField("New Password", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        "Repeat New Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")


class ListingForm(FlaskForm):
    """
    Form for creating or editing a listing.

    Includes custom validation for title, description, and price.
    """

    title = StringField("Title", validators=[DataRequired(), Length(max=128)])
    category = SelectField(
        "Category", coerce=str, validators=[DataRequired()], choices=[]
    )
    description = TextAreaField("Description", validators=[DataRequired()])
    price = FloatField("Price", validators=[Optional()])
    images = MultipleFileField(
        "Listing Images",
        validators=[FileAllowed(["jpg", "jpeg", "png", "gif"], "Images only!")],
    )
    submit = SubmitField("Save")

    def validate_title(self, field):
        """
        Ensure the title contains at least one word.
        """
        if not field.data or len(field.data.strip().split()) < 1:
            raise ValidationError("Title must contain at least one word.")

    def validate_description(self, field):
        """
        Ensure the description is a full sentence with at least four words
        and sentence-ending punctuation.
        """
        import re

        if not field.data or len(re.findall(r"\b\w+\b", field.data)) < 4:
            raise ValidationError(
                "Description must contain at least a sentence with 4 words."
            )
        if not re.search(r"[.!?]", field.data):
            raise ValidationError(
                "Description should end with a sentence-ending punctuation."
            )

    def validate_price(self, field):
        """
        Validate price is non-negative and has at most 2 decimal places.
        """
        if field.data in (None, ""):
            return  # Allow blank
        try:
            value = float(field.data)
        except (TypeError, ValueError):
            raise ValidationError("Price must be a number.")
        if value < 0:
            raise ValidationError("Price cannot be negative.")
        if round(value, 2) != value:
            raise ValidationError("Price must have at most 2 decimal places.")


class CategoryForm(FlaskForm):
    """
    Form for creating or editing categories.
    """

    name = StringField("Category Name", validators=[DataRequired(), Length(max=64)])
    parent_id = SelectField(
        "Parent Category", coerce=str, validators=[Optional()], choices=[]
    )
    submit = SubmitField("Save")

    def validate_name(self, field):
        """
        Validate that the normalized URL name is non-empty and not reserved.

        This runs before any route-level DB checks and provides immediate,
        field-specific feedback to the user.
        """
        raw = field.data or ""
        url_name = generate_url_name(raw)
        if not url_name:
            raise ValidationError(
                "Category name resolves to an empty URL segment; "
                "choose a different name."
            )
        if url_name.lower() in RESERVED_CATEGORY_NAMES:
            raise ValidationError(
                "This name conflicts with system routes; "
                "choose a different name."
            )

    def validate_parent_id(self, field):
        """
        Prevent selecting self or a descendant as parent
        (protects against client tampering).
        Assumes the form sets `self._obj` to the Category instance
        when editing (common pattern).
        """
        parent_id = field.data
        if not parent_id:
            return
        current = getattr(self, "_obj", None)
        if current is None:
            # creating a new category; nothing else to check
            return
        if parent_id == current.id:
            raise ValidationError("Category cannot be its own parent.")
        parent = Category.query.get(parent_id)
        if parent and parent.is_ancestor_of(current):
            raise ValidationError("Selected parent is a descendant of this category.")


class UserEditForm(FlaskForm):
    """
    Form for editing user details and admin status.
    """

    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=64)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=64)])
    is_admin = BooleanField("Administrator")
    submit = SubmitField("Save")
