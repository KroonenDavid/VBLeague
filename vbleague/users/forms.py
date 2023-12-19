from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, DateField, SelectField, BooleanField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from datetime import datetime, timedelta
from vbleague.models import User

def over_18_check(form, field):
    birthdate = field.data
    today = datetime.now().date()

    eighteen_years_ago = today - timedelta(days=365 * 18)

    if birthdate > eighteen_years_ago:
        raise ValidationError('Must be 18 years or older.')


def FileSizeLimit(max_size_in_mb):
    max_bytes = max_size_in_mb * 1024 * 1024

    def file_length_check(form, field):
        if len(field.data.read()) > max_bytes:
            raise ValidationError(f"File size must be less than {max_size_in_mb}MB")
        field.data.seek(0)

    return file_length_check

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    birthday = DateField('Birthday (18+)', validators=[over_18_check])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirmed_password = PasswordField('Confirm Password',
                                       validators=[EqualTo('password', message="Passwords must match")])
    shirt_size = SelectField('Shirt Size', choices=['S', 'M', 'L', 'XL', 'XXL'])
    gender = SelectField('Gender', choices=['Male', 'Female', 'Non-Binary'])
    submit = SubmitField(label="Register")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This e-mail already exists. Please login-in')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    remember = BooleanField('Remember Me')
    submit = SubmitField(label="Log In")

class EditProfile(FlaskForm):
    bio = StringField('Bio')
    profile_pic = FileField('Profile Pic',
                            validators=[FileAllowed(['jpg', 'png', 'jpeg']), FileSizeLimit(max_size_in_mb=10)])
    submit = SubmitField(label="Save Changes")

class RequestResetForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField(label="Request Password Reset")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('There is no account with that email.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirmed_password = PasswordField('Confirm Password',
                                       validators=[EqualTo('password', message="Passwords must match")])
    submit = SubmitField(label="Reset Password")
