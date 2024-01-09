from flask import Blueprint
from flask import render_template, request, url_for, redirect, flash
from vbleague.models import League, Team, Match
from flask_login import login_required
from vbleague.leagues.forms import CreateLeagueForm, LeagueForm
from vbleague import db
from vbleague.users.utils import email_must_be_confirmed
from vbleague.matches.utils import generate_schedule
from flask_login import current_user

matches = Blueprint('matches', __name__)


@matches.route("/leagues/<int:league_id>/schedule")
def schedule(league_id):
    league = db.get_or_404(League, league_id)
    all_leagues = League.query.order_by(League.name).all()

    scheduled_matches = (Match.query.filter(Match.league_id == league_id)
                         .all())

    print(scheduled_matches)

    return render_template('schedule.html', scheduled_matches=scheduled_matches,
                           league=league, all_leagues=all_leagues)


@matches.route('/leagues/<int:league_id>/generate-season')
def generate_season(league_id):
    Match.query.filter_by(league_id=league_id).delete()
    db.session.commit()

    league = db.get_or_404(League, league_id)

    teams = (Team.query.filter(Team.league_id == league_id)
             .filter(Team.name != "Free Agents")
             .order_by(Team.points.desc())
             .order_by(Team.goal_difference.desc())
             .all())

    week_schedule = generate_schedule(3, teams)

    for week, games in enumerate(week_schedule, start=1):
        print(f"Week {week}:")
        for day, match in enumerate(games, start=1):
            print(f"  Match {day}: {match[0]} vs {match[1]}")

            try:
                home_team = match[0].id
            except AttributeError:
                home_team = 'BYE'

            try:
                away_team = match[1].id
            except AttributeError:
                away_team = 'BYE'

            try:
                league_id = match[0].league_id
            except AttributeError:
                league_id = match[1].league_id

            new_match = Match(
                league_id=league_id,
                home_team=home_team,
                away_team=away_team,
                week=week,
            )

            db.session.add(new_match)
            db.session.commit()

    flash('Schedule successfully generated!', 'success')

    return redirect(url_for('matches.schedule', league_id=league.id))
