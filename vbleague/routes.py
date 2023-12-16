from flask import render_template, request, url_for, redirect, flash
from vbleague.models import team_membership, User, League, Team
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.utils import secure_filename
import os
from vbleague.forms import (RegisterForm, LoginForm, TeamLoginForm,
                            CreateTeamForm, CreateLeagueForm, EditProfile,
                            RequestResetForm, ResetPasswordForm)
from vbleague import app, login_manager, db, mail
import secrets
from PIL import Image
from flask_mail import Message


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route("/")
def home():
    return render_template('index.html')


@app.route("/login", methods=["POST", "GET"])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=login_form.remember.data)

            next_page = request.args.get('next')

            return redirect(next_page) if next_page else redirect(url_for('my_profile'))

        else:
            flash('Sorry that password and e-mail combination does not match our records', 'danger')

    return render_template('login.html', form=login_form)


@app.route("/register", methods=["POST", "GET"])
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

        return redirect(url_for('my_profile'))

    return render_template('register.html', form=register_form)


@app.route("/leagues", methods=["POST", "GET"])
def all_leagues():
    leagues = League.query.order_by(League.name).all()

    create_league_form = CreateLeagueForm()

    if create_league_form.validate_on_submit():
        # Make sure to add if statement to catch if league exists already

        new_league = League(
            name=create_league_form.name.data,
            location=create_league_form.location.data,
            days=create_league_form.days.data,
            division=create_league_form.division.data,
            team_size=create_league_form.team_size.data,
            maps_url=create_league_form.maps_url.data,
        )

        db.session.add(new_league)
        db.session.commit()

        new_team = Team(
            name="Free Agents",
            description="Free Agent List",
            league_id=new_league.id,
            password="jiojasdoijiooajisdoijasd",
            captain_id=1,
        )

        db.session.add(new_team)
        db.session.commit()

        return redirect(url_for('all_leagues'))

    return render_template('leagues.html', all_leagues=leagues, form=create_league_form)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images/profile_pics', picture_fn)

    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/my-profile", methods=["POST", "GET"])
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
                old_profile_pic_path = os.path.join(app.root_path, 'static/images/profile_pics', old_profile_pic)
                if os.path.exists(old_profile_pic_path):
                    os.remove(old_profile_pic_path)

        db.session.commit()

        return redirect(url_for('my_profile'))

    elif request.method == 'GET':
        edit_profile_form.bio.data = current_user.bio

    image_file = url_for('static', filename=f'images/profile_pics/{current_user.profile_pic}')

    return render_template('profile.html', form=edit_profile_form, image_file=image_file)


@app.route("/leagues/<int:chosen_league_id>")
def user_chosen_league(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    return render_template('selected_league.html', league=league)


#
# @app.route("/leagues/<string:chosen_league>/<string:chosen_standings>")
# def user_chosen_league_standings(chosen_league, chosen_standings):
#     pass
#
# @app.route("/leagues/<string:chosen_league>/<string:chosen_fixtures>")
# def user_chosen_league_standings(chosen_league, chosen_fixtures):
#     pass
#
# @app.route("/leagues/<string:chosen_league>/<string:chosen_stats>")
# def user_chosen_stats_page(chosen_league, chosen_stats):
#     pass
#
@app.route("/leagues/<int:chosen_league_id>/join")
@login_required
def join_chosen_league(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    return render_template('join.html', league=league)


@app.route("/leagues/<int:chosen_league_id>/free-agent")
@login_required
def join_chosen_league_free(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    return render_template('free-agent-join.html', league=league)


@app.route("/leagues/<int:chosen_league_id>/teams")
def show_all_teams(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)

    return render_template('teams.html', league=league)


@app.route("/leagues/<int:chosen_league_id>/teams/free-agents/join")
@login_required
def join_free_agents(chosen_league_id):
    free_agents_team = Team.query.filter_by(name="Free Agents", league_id=chosen_league_id).first()

    is_on_team = any(
        db.session.query(team_membership)
        .filter(team_membership.c.user_id == current_user.id)
        .join(Team, Team.id == team_membership.c.team_id)
        .filter(Team.league_id == chosen_league_id)
        .all()
    )

    if is_on_team:
        flash('You are already on the free agents team.')
        return redirect(url_for('my_profile'))

    free_agents_team.players.append(current_user)
    db.session.commit()

    return redirect(url_for('team_page', chosen_league_id=chosen_league_id, team_id=free_agents_team.id))


@app.route("/leagues/<int:chosen_league_id>/teams/<int:team_id>/join", methods=['POST', 'GET'])
@login_required
def join_chosen_team(chosen_league_id, team_id):
    league = db.get_or_404(League, chosen_league_id)
    team = db.get_or_404(Team, team_id)

    team_login = TeamLoginForm()

    if team_login.validate_on_submit():
        if current_user in team.players:
            flash('You are already on this team.')
            return redirect(url_for('join_chosen_team', chosen_league_id=chosen_league_id, team_id=team_id))

        password = team_login.password.data

        if password == team.password:

            team.players.append(current_user)
            db.session.commit()

            return redirect(url_for('team_page', chosen_league_id=chosen_league_id, team_id=team.id))

        else:
            flash('Sorry, that is the wrong password.')
            return redirect(url_for('join_chosen_team', chosen_league_id=chosen_league_id, team_id=team_id))

    return render_template('join-team.html', league=league, team=team, form=team_login)


@app.route("/leagues/<int:chosen_league_id>/create-team", methods=["POST", "GET"])
@login_required
def create_team(chosen_league_id):
    team_form = CreateTeamForm()
    league = db.get_or_404(League, chosen_league_id)

    if request.method == "POST":

        is_on_team = any(
            db.session.query(team_membership)
            .filter(team_membership.c.user_id == current_user.id)
            .join(Team, Team.id == team_membership.c.team_id)
            .filter(Team.league_id == chosen_league_id)
            .all()
        )

        if is_on_team:
            flash('You are already on a team in this league.')
            return redirect(url_for('create_team', chosen_league_id=chosen_league_id))

        existing_team = Team.query.filter_by(name=team_form.name.data, league_id=chosen_league_id).first()

        if existing_team:
            flash('This team name is taken.')
            return redirect(url_for('create_team', chosen_league_id=chosen_league_id))

        new_team = Team(
            name=team_form.name.data,
            description=team_form.description.data,
            logo=team_form.logo.data,
            league_id=chosen_league_id,
            password=team_form.password.data,
            captain_id=current_user.id,
        )

        if team_form.logo.data:
            picture_file = save_picture(team_form.logo.data)
            new_team.logo = picture_file

        new_team.players.append(current_user)

        db.session.add(new_team)
        db.session.commit()

        return redirect(url_for('team_page', chosen_league_id=chosen_league_id, team_id=new_team.id))

    return render_template('create_team.html', league=league, form=team_form)


@app.route('/leagues/<int:chosen_league_id>/teams/<int:team_id>')
def team_page(chosen_league_id, team_id):
    league = db.get_or_404(League, chosen_league_id)
    team = db.get_or_404(Team, team_id)

    return render_template('team_page.html', league=league, team=team)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/players/<int:player_id>')
def player_profile(player_id):
    player = db.get_or_404(User, player_id)
    image_file = url_for('static', filename=f'images/profile_pics/{player.profile_pic}')
    return render_template('player-profile.html', player=player, image_file=image_file)


@app.route('/remove-player-from-team')
@login_required
def remove_player_from_team():
    player_id = request.args.get('player_id')
    team_id = request.args.get('team_id')
    league_id = request.args.get('league_id')

    player = db.get_or_404(User, player_id)
    team = db.get_or_404(Team, team_id)

    team.players.remove(player)
    flash('Successfully left team.')

    db.session.commit()
    return redirect(request.referrer)


@app.route('/remove-team')
@login_required
def remove_team():
    team_id = request.args.get('team_id')
    league_id = request.args.get('league_id')

    team = db.get_or_404(Team, team_id)
    league = db.get_or_404(League, league_id)

    league.teams.remove(team)
    flash('Successfully deleted team.')

    db.session.commit()

    if request.args.get('team_page'):
        return redirect(url_for('my-profile'))

    return redirect(request.referrer)


@app.route('/remove-league')
@login_required
def remove_league():
    league_id = request.args.get('chosen_league_id')
    league = db.get_or_404(League, league_id)

    db.session.delete(league)
    db.session.commit()

    flash('League deleted successfully')

    return redirect(url_for('all_leagues', league=league))

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender=os.getenv('EMAIL'),
                  recipients=[user.email])
    msg.body = (f'To reset your password, visit the following link\n'
                f'{url_for("reset_token", token=token, _external=True)}\n'
                f'If you did not make this request then simply ignore this email.')

    mail.send(msg)
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RequestResetForm ()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password', 'info')
        return redirect(url_for('login'))


    return render_template('reset_request.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()

    if form.validate_on_submit():
        hash_and_salted_pass = generate_password_hash(password=form.password.data, method='pbkdf2:sha256',
                                                      salt_length=8)

        user.password = hash_and_salted_pass

        db.session.commit()

        flash('Password successfully reset, please log-in')
        return redirect(url_for('login'))

    return render_template('reset_token.html', form=form)

