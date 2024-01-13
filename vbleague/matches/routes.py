from flask import Blueprint
from flask import render_template, request, url_for, redirect, flash
from vbleague.models import League, Team, Match, match_membership, User, PlayerStats
from flask_login import login_required
from vbleague.leagues.forms import CreateLeagueForm, LeagueForm
from vbleague.matches.forms import PreMatchInfoForm, PostMatchInfoForm, HighlightsForm, PlayerMatchStats
from vbleague import db
from vbleague.users.utils import email_must_be_confirmed, must_be_admin
from vbleague.matches.utils import generate_schedule, update_match_results
from flask_login import current_user
from sqlalchemy import or_

matches = Blueprint('matches', __name__)


@matches.route("/leagues/<int:league_id>/schedule")
def schedule(league_id):
    league = db.get_or_404(League, league_id)
    all_leagues = League.query.order_by(League.name).all()

    scheduled_matches = (Match.query.filter(Match.league_id == league_id)
                         .all())

    dates_by_week = {}
    for match in scheduled_matches:
        week = match.week
        if week not in dates_by_week:
            dates_by_week[week] = []
        if match.date != 'TBD' and not dates_by_week[week]:
            dates_by_week[week].append(match.date)

    return render_template('schedule.html',
                           scheduled_matches=scheduled_matches,
                           league=league,
                           all_leagues=all_leagues,
                           dates_by_week=dates_by_week)


@matches.route('/leagues/<int:league_id>/match/<int:match_id>')
def match_page(league_id, match_id):
    league = db.get_or_404(League, league_id)
    match = db.get_or_404(Match, match_id)

    return render_template('match_page.html', league=league, match=match)


@matches.route('/leagues/<int:league_id>/generate-season')
@must_be_admin
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
        for day, match in enumerate(games, start=1):
            try:
                home_team = match[0]
            except AttributeError:
                home_team = 'BYE'

            try:
                away_team = match[1]
            except AttributeError:
                away_team = 'BYE'

            try:
                league_id = match[0].league_id
            except AttributeError:
                league_id = match[1].league_id

            new_match = Match(
                league_id=league_id,
                home_team=home_team.id,
                away_team=away_team.id,
                week=week,
            )

            db.session.add(new_match)
            db.session.commit()

            for player in home_team.players:
                player_stats = PlayerStats(
                    match=new_match,
                    team=home_team,
                    user=player
                )
                db.session.add(player_stats)

                # Create PlayerStats entries for away team players
            for player in away_team.players:
                player_stats = PlayerStats(
                    match=new_match,
                    team=away_team,
                    user=player
                )
                db.session.add(player_stats)

            db.session.commit()

    flash('Schedule successfully generated!', 'success')

    return redirect(url_for('matches.schedule', league_id=league.id))


@matches.route('/leagues/<int:league_id>/match/<int:match_id>/edit', methods=['GET', 'POST'])
@must_be_admin
def match_info(league_id, match_id):
    league = db.get_or_404(League, league_id)
    match = db.get_or_404(Match, match_id)

    pre_match_form = PreMatchInfoForm()
    post_match_form = PostMatchInfoForm()
    highlights_link_form = HighlightsForm()

    if pre_match_form.validate_on_submit():
        match.date = pre_match_form.date.data
        match.time = pre_match_form.time.data
        match.field = pre_match_form.field.data

        flash('Pre-match info successfully submitted!', 'success')

        db.session.commit()

        return redirect(url_for('matches.schedule', league_id=league.id))

    if post_match_form.validate_on_submit():
        update_match_results(match, post_match_form)

        flash('Scores successfully submitted!', 'success')

        db.session.commit()

        return redirect(url_for('matches.schedule', league_id=league.id))

    if highlights_link_form.validate_on_submit():
        match.highlights_link = highlights_link_form.highlights_link.data

        flash('Highlights link successfully submitted!', 'success')

        db.session.commit()

    return render_template('match_info.html',
                           league=league,
                           match=match,
                           pre_match_form=pre_match_form,
                           post_match_form=post_match_form,
                           highlights_link_form=highlights_link_form)


@matches.route('/leagues/<int:league_id>/match/<int:match_id>/team/<int:team_id>player/<int:player_id>/edit', methods=['GET','POST'])
def stats_page(league_id, match_id, player_id, team_id):
    league = db.get_or_404(League, league_id)
    match = db.get_or_404(Match, match_id)
    player = db.get_or_404(User, player_id)
    team = db.get_or_404(Team, team_id)

    form = PlayerMatchStats()

    if form.validate_on_submit():
        stat = PlayerStats.query.filter_by(
            match_id=match.id,
            team_id=team.id,
            user_id=player.id,
        ).first()

        stat.goals_scored = form.goals_scored.data
        stat.assists = form.assists.data
        stat.saves_made = form.saves_made.data
        stat.goals_against = form.goals_against.data
        stat.match_played = form.match_played.data

        db.session.commit()

        flash('Stats submitted successfully', 'success')

        return redirect(url_for('matches.match_page', league_id=league.id, match_id=match.id))

    return render_template('stats_entry.html',
                           league=league,
                           match=match,
                           player=player,
                           form=form)
