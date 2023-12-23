from flask import url_for
import os
from vbleague import mail
import secrets
from PIL import Image
from flask_mail import Message
from flask import current_app, redirect, flash
from functools import wraps
from flask_login import current_user


def save_picture(form_picture):
    """Save Picture

    Takes picture user uploaded in form and saves picture under static/images/profile_pics
    as a random 8-digit hex combination. Also saves it as a 500x500 image.

    :param form_picture:
    :return: filename
    """
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/images/profile_pics', picture_fn)

    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def send_reset_email(user):
    """Send Reset E-Mail

        Calls the get_reset_token function to assign user a token and sends user an email with a token
        that is valid for 30 minutes.

        :param user:
        """
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender=os.getenv('EMAIL'),
                  recipients=[user.email])
    msg.body = (f'To reset your password, visit the following link\n'
                f'{url_for("users.reset_token", token=token, _external=True)}\n'
                f'If you did not make this request then simply ignore this email.')

    mail.send(msg)


def send_email_confirm(user):
    """Send E-mail Confirmation

            Calls the get_reset_token function to assign user a token and sends user an email with a token
            that is valid for 30 minutes.

            :param user:
            """
    token = user.get_reset_token()
    msg = Message('VBLeague | Validate Your Email',
                  sender=os.getenv('EMAIL'),
                  recipients=[user.email])
    msg.body = (f'Thank you for signing up to VBLeague. To confirm your email, visit the following link\n'
                f'{url_for("users.confirm_email_token", token=token, _external=True)}\n'
                f'Please note this link will expire in 30 minutes.')

    mail.send(msg)


def email_must_be_confirmed(function):
    '''
    Email Confirmation Decorator Function\n
    Checks to see if user's email has been confirmed. If not they get re-directed to the homepage.
    Flashes to tell user they can only continue with their email confirmed.
    :param function:
    :return: redirect(url_for('main.home')):
    '''

    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user.email_confirmed:
            flash('You must confirm your email to continue', 'danger')
            return redirect(url_for('main.home'))
        return function(*args, **kwargs)

    return wrapper

def send_player_invite(captain_team, captain, invited_player, msg_body):
    token = captain_team.generate_join_token()
    msg = Message(f'VBLeague | {captain.name} has invited you to {captain_team.name}',
                  sender=os.getenv('EMAIL'),
                  recipients=[invited_player.email])
    msg.body = (f'Hey {invited_player.name}, {captain.name} has invited you to {captain_team.name}!\n\n'
                f'"{msg_body}"\n\n'
                f'If you want to join, click the link below!\n'
                f'{url_for("teams.confirm_join_link", token=token, _external=True, league_id=captain_team.parent_league.id, team_id=captain_team.id)}\n'
                f'If you wish to contact the captain please email them at {captain.email}')

    mail.send(msg)


