# Created by GitHub Copilot for Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu)

"""
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
        Ensure the description is a full sentence with at least four words and sentence-ending punctuation.
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
        "Parent Category", coerce=int, validators=[Optional()], choices=[]
    )
    submit = SubmitField("Save")


class UserEditForm(FlaskForm):
    """
    Form for editing user details and admin status.
    """

    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=64)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=64)])
    is_admin = BooleanField("Administrator")
    submit = SubmitField("Save")
