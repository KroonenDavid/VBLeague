from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, DateField, SelectField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_ckeditor import CKEditorField
from datetime import datetime, timedelta


def over_18_check(form, field):
    birthdate = field.data
    today = datetime.now().date()

    eighteen_years_ago = today - timedelta(days=365 * 18)

    if birthdate > eighteen_years_ago:
        raise ValidationError('Must be 18 years or older.')


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


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField(label="Log In")


class TeamLoginForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField(label="Log In")


class CreateTeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired()])
    description = StringField('Team Description', validators=[DataRequired()])
    password = StringField('Password')
    logo = FileField('Logo')
    submit = SubmitField(label="Create Team")


class EditProfile(FlaskForm):
    bio = StringField('Bio')
    profile_pic = FileField('Profile Pic')
    submit = SubmitField(label="Save Changes")


class LeagueForm(FlaskForm):
    bio = CKEditorField("Bio", validators=[DataRequired()])
    submit = SubmitField("Submit Bio")

class CreateLeagueForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    location = StringField(validators=[DataRequired()])
    days = StringField(validators=[DataRequired()])
    division = StringField(validators=[DataRequired()])
    team_size = StringField(validators=[DataRequired()])
    maps_url = StringField(validators=[DataRequired()])
    submit = SubmitField("Add")
