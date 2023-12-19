from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField

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
