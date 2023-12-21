from flask import render_template, request, url_for, redirect, flash, Blueprint
from vbleague.models import team_membership, User, League, Team
from flask_login import login_required, current_user
from vbleague.teams.forms import TeamLoginForm, CreateTeamForm
from vbleague import db
from vbleague.users.utils import save_picture

teams = Blueprint('teams', __name__)

@teams.route("/leagues/<int:chosen_league_id>/teams")
def show_all_teams(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)

    return render_template('teams.html', league=league)

@teams.route('/leagues/<int:chosen_league_id>/teams/<int:team_id>')
def team_page(chosen_league_id, team_id):
    league = db.get_or_404(League, chosen_league_id)
    team = db.get_or_404(Team, team_id)

    return render_template('team_page.html', league=league, team=team)

@teams.route('/leagues/<int:chosen_league_id>/free-agents')
def free_agents(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    free_agents_team = Team.query.filter_by(name="Free Agents", league_id=chosen_league_id).first()

    is_captain = any(
            db.session.query(Team)
            .filter(Team.captain_id == current_user.id)
            .all()
        )

    if is_captain:
        return render_template('free_agents.html', league=league, team=free_agents_team)

    else:
        flash('Sorry you have to be a captain to see the free agent list.', 'warning')
        return redirect(request.referrer)

@teams.route("/leagues/<int:chosen_league_id>/teams/<int:team_id>/join", methods=['POST', 'GET'])
@login_required
def join_chosen_team(chosen_league_id, team_id):
    league = db.get_or_404(League, chosen_league_id)
    team = db.get_or_404(Team, team_id)

    team_login = TeamLoginForm()

    if team_login.validate_on_submit():
        if current_user in team.players:
            flash('You are already on this team.')
            return redirect(url_for('teams.join_chosen_team', chosen_league_id=chosen_league_id, team_id=team_id))

        password = team_login.password.data

        if password == team.password:
            flash(f'{team.name} joined successfully!', 'success')
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

    if request.method == "POST":

        is_on_team = any(
            db.session.query(team_membership)
            .filter(team_membership.c.user_id == current_user.id)
            .join(Team, Team.id == team_membership.c.team_id)
            .filter(Team.league_id == chosen_league_id)
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


