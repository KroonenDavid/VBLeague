from flask import Blueprint
from flask import render_template, request, url_for, redirect, flash
from vbleague.models import League, Team
from flask_login import login_required
from vbleague.leagues.forms import CreateLeagueForm
from vbleague import db

leagues = Blueprint('leagues', __name__)

@leagues.route("/leagues", methods=["POST", "GET"])
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

        return redirect(url_for('leagues.all_leagues'))

    return render_template('leagues.html', all_leagues=leagues, form=create_league_form)

@leagues.route("/leagues/<int:chosen_league_id>")
def user_chosen_league(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    return render_template('selected_league.html', league=league)
@leagues.route("/leagues/<int:chosen_league_id>/join")
@login_required
def join_chosen_league(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    return render_template('join.html', league=league)
@leagues.route("/leagues/<int:chosen_league_id>/free-agent")
@login_required
def join_chosen_league_free(chosen_league_id):
    league = db.get_or_404(League, chosen_league_id)
    return render_template('free-agent-join.html', league=league)

@leagues.route('/remove-league')
@login_required
def remove_league():
    league_id = request.args.get('chosen_league_id')
    league = db.get_or_404(League, league_id)

    db.session.delete(league)
    db.session.commit()

    flash('League deleted successfully')

    return redirect(url_for('leagues.all_leagues', league=league))

