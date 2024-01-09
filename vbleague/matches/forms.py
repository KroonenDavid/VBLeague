from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField

class CreateMatchForm(FlaskForm):
    home_team = StringField(validators=[DataRequired()])
    home_team_score = IntegerField(validators=[DataRequired()])
    away_team_score = IntegerField(validators=[DataRequired()])
    date = StringField(validators=[DataRequired()])
    field = StringField(validators=[DataRequired()])
    highlights_link = StringField(validators=[DataRequired()])
    submit = SubmitField("Add")