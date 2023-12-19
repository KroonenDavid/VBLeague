from flask import render_template, request, url_for, redirect, flash, Blueprint, current_app
from vbleague.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user
import os
from vbleague.users.forms import (RegisterForm, LoginForm, EditProfile,
                            RequestResetForm, ResetPasswordForm)
from vbleague import db
from vbleague.users.utils import save_picture, send_reset_email




users = Blueprint('users', __name__)

@users.route("/login", methods=["POST", "GET"])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=login_form.remember.data)

            next_page = request.args.get('next')

            return redirect(next_page) if next_page else redirect(url_for('users.my_profile'))

        else:
            flash('Sorry that password and e-mail combination does not match our records', 'danger')

    return render_template('login.html', form=login_form)


@users.route("/register", methods=["POST", "GET"])
def register():
    register_form = RegisterForm()

    if register_form.validate_on_submit():
        hash_and_salted_pass = generate_password_hash(password=register_form.password.data, method='pbkdf2:sha256',
                                                      salt_length=8)

        new_user = User(
            name=register_form.name.data,
            email=register_form.email.data,
            birthdate=register_form.birthday.data,
            password=hash_and_salted_pass,
            shirt_size=register_form.shirt_size.data,
            gender=register_form.gender.data,
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect(url_for('users.my_profile'))

    return render_template('register.html', form=register_form)

@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@users.route('/players/<int:player_id>')
def player_profile(player_id):
    player = db.get_or_404(User, player_id)
    image_file = url_for('static', filename=f'images/profile_pics/{player.profile_pic}')
    return render_template('player-profile.html', player=player, image_file=image_file)


@users.route("/my-profile", methods=["POST", "GET"])
@login_required
def my_profile():
    edit_profile_form = EditProfile()

    if edit_profile_form.validate_on_submit():
        current_user.bio = edit_profile_form.bio.data

        old_profile_pic = current_user.profile_pic

        if edit_profile_form.profile_pic.data:
            picture_file = save_picture(edit_profile_form.profile_pic.data)
            current_user.profile_pic = picture_file

            if old_profile_pic and old_profile_pic != 'Default_pfp.png':
                old_profile_pic_path = os.path.join(current_app.root_path, 'static/images/profile_pics', old_profile_pic)
                if os.path.exists(old_profile_pic_path):
                    os.remove(old_profile_pic_path)

        db.session.commit()

        return redirect(url_for('users.my_profile'))

    elif request.method == 'GET':
        edit_profile_form.bio.data = current_user.bio

    image_file = url_for('static', filename=f'images/profile_pics/{current_user.profile_pic}')

    return render_template('profile.html', form=edit_profile_form, image_file=image_file)

@users.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RequestResetForm ()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password', 'info')
        return redirect(url_for('users.login'))


    return render_template('reset_request.html', form=form)

@users.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()

    if form.validate_on_submit():
        hash_and_salted_pass = generate_password_hash(password=form.password.data, method='pbkdf2:sha256',
                                                      salt_length=8)

        user.password = hash_and_salted_pass

        db.session.commit()

        flash('Password successfully reset, please log-in')
        return redirect(url_for('users.login'))

    return render_template('reset_token.html', form=form)