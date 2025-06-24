# Created by GitHub Copilot for Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu)

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send reset link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class ItemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=128)])
    type = SelectField('Type', coerce=int, validators=[DataRequired()])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[Optional()])
    images = MultipleFileField('Item Images', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Save')

class TypeForm(FlaskForm):
    name = StringField('Type Name', validators=[DataRequired(), Length(max=32)])
    submit = SubmitField('Save')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=64)])
    type_id = SelectField('Type', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

class UserEditForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    is_admin = BooleanField('Administrator')
    submit = SubmitField('Save')