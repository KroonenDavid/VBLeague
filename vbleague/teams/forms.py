from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, ValidationError
def FileSizeLimit(max_size_in_mb):
    max_bytes = max_size_in_mb * 1024 * 1024

    def file_length_check(form, field):
        if len(field.data.read()) > max_bytes:
            raise ValidationError(f"File size must be less than {max_size_in_mb}MB")
        field.data.seek(0)

    return file_length_check

class TeamLoginForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField(label="Log In")


class CreateTeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired()])
    description = StringField('Team Description', validators=[DataRequired()])
    password = StringField('Password')
    logo = FileField('Logo', validators=[FileAllowed(['jpg', 'png', 'jpeg']), FileSizeLimit(max_size_in_mb=10)])
    submit = SubmitField(label="Create Team")
class InvitePlayerForm(FlaskForm):
    body = StringField('Invite Message', validators=[DataRequired()])
    submit = SubmitField(label='Invite')


