from flask import Blueprint
from flask import render_template, request, url_for, redirect, flash
from vbleague.models import League, Team
from flask_login import login_required
from vbleague.leagues.forms import CreateLeagueForm, LeagueForm
from vbleague import db
from vbleague.users.utils import email_must_be_confirmed
from flask_login import current_user

leagues = Blueprint('leagues', __name__)

@leagues.route("/leagues", methods=["POST", "GET"])
def all_leagues():
    leagues = League.query.order_by(League.name).all()

    create_league_form = CreateLeagueForm()

    if create_league_form.validate_on_submit():
        existing_league = League.query.filter_by(name=create_league_form.name.data).first()

        if existing_league:
            flash('This league name already exists', 'danger')
            return redirect(url_for('leagues.all_leagues'))

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

        flash('League added successfully', 'info')

        db.session.add(new_team)
        db.session.commit()

        return redirect(url_for('leagues.all_leagues'))

    return render_template('leagues.html', all_leagues=leagues, form=create_league_form)

@leagues.route("/leagues/<int:chosen_league_id>")
def user_chosen_league(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    return render_template('selected_league.html', league=league)

@leagues.route("/leagues/<int:chosen_league_id>/edit", methods=['POST', 'GET'])
def edit_league(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    form = LeagueForm()

    if not current_user.is_admin:
        return render_template('errors/403.html')

    if form.validate_on_submit():
        league.bio = form.bio.data

        flash('Bio changed successfully!', 'success')

        db.session.commit()

        return redirect(url_for('leagues.user_chosen_league', chosen_league_id=league.id))
    elif request.method == 'GET':
        form.bio.data = league.bio

    return render_template('edit_league.html', league=league, form=form)


@leagues.route("/leagues/<int:chosen_league_id>/join")
@login_required
@email_must_be_confirmed
def join_chosen_league(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    return render_template('join.html', league=league)
@leagues.route("/leagues/<int:chosen_league_id>/free-agent")
@login_required
@email_must_be_confirmed
def join_chosen_league_free(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    return render_template('free-agent-join.html', league=league)

@leagues.route('/remove-league')
@login_required
def remove_league():
    if current_user.is_admin:
        league_id = request.args.get('chosen_league_id')
        league = db.get_or_404(League, league_id)

        db.session.delete(league)
        db.session.commit()

        flash('League deleted successfully', 'info')

        return redirect(url_for('leagues.all_leagues', league=league))
    else:
        return render_template('errors/403.html')

