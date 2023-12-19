from flask import url_for
import os
from vbleague import mail
import secrets
from PIL import Image
from flask_mail import Message
from flask import current_app

def save_picture(form_picture):
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
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender=os.getenv('EMAIL'),
                  recipients=[user.email])
    msg.body = (f'To reset your password, visit the following link\n'
                f'{url_for("reset_token", token=token, _external=True)}\n'
                f'If you did not make this request then simply ignore this email.')

    mail.send(msg)

