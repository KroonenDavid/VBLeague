from flask import render_template, request, url_for, redirect, flash, Blueprint
from vbleague.models import team_membership, User, League, Team
from flask_login import login_required, current_user
from vbleague.teams.forms import TeamLoginForm, CreateTeamForm, InvitePlayerForm
from vbleague import db
from vbleague.users.utils import save_picture, send_player_invite

teams = Blueprint('teams', __name__)

@teams.route("/leagues/<int:chosen_league_id>/teams")
def show_all_teams(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)

    return render_template('teams.html', league=league)

@teams.route('/leagues/<int:chosen_league_id>/teams/<int:team_id>')
def team_page(chosen_league_id, team_id):
    league = db.get_or_404(League, chosen_league_id)
    team = db.get_or_404(Team, team_id)

    token = team.generate_join_token()
    join_link = url_for("teams.confirm_join_link", token=token, _external=True, league_id=chosen_league_id, team_id=team_id)

    image_file = url_for('static', filename=f'images/profile_pics/{team.logo}')

    return render_template('team_page.html', league=league, team=team, image_file=image_file, join_link=join_link)

@teams.route('/leagues/<int:chosen_league_id>/free-agents', methods=['GET'])
def free_agents(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    free_agents_team = Team.query.filter_by(name="Free Agents", league_id=chosen_league_id).first()
    team_id = request.args.get('team_id')
    captain_team = db.get_or_404(Team, team_id)

    is_captain = any(
            db.session.query(Team)
            .filter(Team.captain_id == current_user.id)
            .all()
        )

    if is_captain:

        return render_template('free_agents.html', league=league, team=free_agents_team, captain_team=captain_team)

    else:
        flash('Sorry you have to be a captain to see the free agent list.', 'warning')
        return redirect(request.referrer)

@teams.route("/invite-player/<int:player_id>", methods=['POST', 'GET'])
@login_required
def invite_player(player_id):
    captain_team_id = request.args.get('captain_team_id')
    captain_team = db.get_or_404(Team, captain_team_id)

    form = InvitePlayerForm()
    invited_player = db.get_or_404(User, player_id)

    is_captain = any(
        db.session.query(Team)
        .filter(Team.captain_id == current_user.id)
        .all()
    )

    if is_captain:
        if form.validate_on_submit():
            send_player_invite(captain_team, captain=current_user, invited_player=invited_player, msg_body=form.body.data)
            flash(f'Successfully invited {invited_player.name}', 'success')
            return redirect(url_for('teams.free_agents', team_id=captain_team_id, chosen_league_id=captain_team.parent_league.id))
        return render_template('invite-player.html', captain_team=captain_team, invited_player=invited_player, form=form)

    else:
        flash('Sorry you have to be a captain to see the free agent list.', 'warning')
        return redirect(request.referrer)

@teams.route("/leagues/<int:chosen_league_id>/teams/<int:team_id>/join", methods=['POST', 'GET'])
@login_required
def join_chosen_team(chosen_league_id, team_id):
    league = db.get_or_404(League, chosen_league_id)
    team = db.get_or_404(Team, team_id)

    free_agents_team = (
        Team.query
        .filter_by(name="Free Agents", league_id=chosen_league_id)
        .first()
    )

    team_login = TeamLoginForm()

    if team_login.validate_on_submit():
        if current_user in team.players:
            flash('You are already on this team.')
            return redirect(url_for('teams.join_chosen_team', chosen_league_id=chosen_league_id, team_id=team_id))

        password = team_login.password.data

        if password == team.password:
            flash(f'{team.name} joined successfully!', 'success')

            if free_agents_team in current_user.teams_joined:
                free_agents_team.players.remove(current_user)

            team.players.append(current_user)
            db.session.commit()

            return redirect(url_for('teams.team_page', chosen_league_id=chosen_league_id, team_id=team.id))

        else:
            flash('Sorry, that is the wrong password.')
            return redirect(url_for('teams.join_chosen_team', chosen_league_id=chosen_league_id, team_id=team_id))

    return render_template('join-team.html', league=league, team=team, form=team_login)


@teams.route("/leagues/<int:chosen_league_id>/create-team", methods=["POST", "GET"])
@login_required
def create_team(chosen_league_id):
    team_form = CreateTeamForm()
    league = db.get_or_404(League, chosen_league_id)

    free_agents_team = (
        Team.query
        .filter_by(name="Free Agents", league_id=chosen_league_id)
        .first()
    )

    if request.method == "POST":

        is_on_team = any(
            db.session.query(team_membership)
            .filter(team_membership.c.user_id == current_user.id)
            .join(Team, Team.id == team_membership.c.team_id)
            .filter(Team.league_id == chosen_league_id)
            .filter(Team.name != "Free Agents")
            .all()
        )

        if is_on_team:
            flash('You are already on a team in this league.', 'danger')
            return redirect(url_for('teams.create_team', chosen_league_id=chosen_league_id))

        existing_team = Team.query.filter_by(name=team_form.name.data, league_id=chosen_league_id).first()

        if existing_team:
            flash('This team name is taken.', 'danger')
            return redirect(url_for('teams.create_team', chosen_league_id=chosen_league_id))

        new_team = Team(
            name=team_form.name.data,
            description=team_form.description.data,
            logo=team_form.logo.data,
            league_id=chosen_league_id,
            password=team_form.password.data,
            captain_id=current_user.id,
        )

        if free_agents_team in current_user.teams_joined:
            free_agents_team.players.remove(current_user)

        if team_form.logo.data:
            picture_file = save_picture(team_form.logo.data)
            new_team.logo = picture_file

        new_team.players.append(current_user)

        flash('Team created successfully!', 'success')

        db.session.add(new_team)
        db.session.commit()

        return redirect(url_for('teams.team_page', chosen_league_id=chosen_league_id, team_id=new_team.id))

    return render_template('create_team.html', league=league, form=team_form)


@teams.route("/leagues/<int:chosen_league_id>/teams/free-agents/join")
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
        flash('You are already on the free agents team.', 'warning')
        return redirect(url_for('users.my_profile'))

    free_agents_team.players.append(current_user)
    db.session.commit()
    flash('Successfully joined the free agents! Wait to be invited to a team or contact a captain!',
          'success')

    return redirect(url_for('teams.team_page', chosen_league_id=chosen_league_id, team_id=free_agents_team.id))
@teams.route('/remove-player-from-team')
@login_required
def remove_player_from_team():
    player_id = request.args.get('player_id')
    team_id = request.args.get('team_id')
    league_id = request.args.get('league_id')

    player = db.get_or_404(User, player_id)
    team = db.get_or_404(Team, team_id)

    team.players.remove(player)
    flash('Successfully left team.', 'info')

    db.session.commit()
    return redirect(request.referrer)


@teams.route('/remove-team')
@login_required
def remove_team():
    team_id = request.args.get('team_id')
    league_id = request.args.get('league_id')

    team = db.get_or_404(Team, team_id)
    league = db.get_or_404(League, league_id)

    league.teams.remove(team)
    flash('Successfully deleted team.', 'success')

    db.session.commit()

    if request.args.get('team_page'):
        return redirect(url_for('users.my-profile'))

    return redirect(request.referrer)

@teams.route('/leagues/<int:league_id>/teams/<int:team_id>/join/<token>', methods=['GET'])
@login_required
def confirm_join_link(league_id, team_id, token):

    league = db.get_or_404(League, league_id)
    team = Team.verify_join_token(token)
    if team is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('main.home'))

    if current_user in team.players:
        flash('You are already on this team!', 'info')
        return redirect(url_for('users.my_profile'))

    flash(f'You joined {team.name} successfully!', 'success')

    team.players.append(current_user)
    db.session.commit()

    return redirect(url_for('teams.team_page', team_id=team.id, chosen_league_id=league.id))





