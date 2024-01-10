from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length
from flask_ckeditor import CKEditorField

class PreMatchInfoForm(FlaskForm):
    date = StringField(validators=[DataRequired()])
    time = StringField(validators=[DataRequired()])
    field = StringField(validators=[DataRequired()])

    submit = SubmitField("Add")

class PostMatchInfoForm(FlaskForm):
    home_team_score = StringField(validators=[DataRequired(), Length(max=2)], render_kw={'style': 'width: 5ch; text-align: center'})
    away_team_score = StringField(validators=[DataRequired(), Length(max=2)], render_kw={'style': 'width: 5ch; text-align: center'})
    highlights_link = StringField()

    submit = SubmitField("Add")

class HighlightsForm(FlaskForm):
    highlights_link = StringField()

    submit = SubmitField("Add")