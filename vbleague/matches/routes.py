from flask import Blueprint
from flask import render_template, request, url_for, redirect, flash
from vbleague.models import League, Team, Match
from flask_login import login_required
from vbleague.leagues.forms import CreateLeagueForm, LeagueForm
from vbleague.matches.forms import PreMatchInfoForm, PostMatchInfoForm, HighlightsForm
from vbleague import db
from vbleague.users.utils import email_must_be_confirmed, must_be_admin
from vbleague.matches.utils import generate_schedule
from flask_login import current_user
from sqlalchemy import or_

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

@matches.route('/leagues/<int:league_id>/matches/<int:match_id>/info', methods=['GET', 'POST'])
@must_be_admin
def match_info(league_id, match_id):
    league = db.get_or_404(League, league_id)
    match = db.get_or_404(Match, match_id)
    teams = Team.query.filter(or_(Team.id == match.home_team, Team.id == match.away_team)).all()

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
        initial_away_score = match.away_team_score
        initial_home_score = match.home_team_score

        if not match.been_played:
            if int(post_match_form.home_team_score.data) > int(post_match_form.away_team_score.data):
                match.home_team_info.matches_won += 1
                match.away_team_info.matches_lost += 1

            elif int(post_match_form.home_team_score.data) < int(post_match_form.away_team_score.data):
                match.home_team_info.matches_lost += 1
                match.away_team_info.matches_won += 1

            else:
                match.home_team_info.matches_tied += 1
                match.away_team_info.matches_tied += 1

        else:
            match.home_team_info.goals_for -= initial_home_score
            match.home_team_info.goals_against -= initial_away_score

            match.away_team_info.goals_for -= initial_away_score
            match.away_team_info.goals_against -= initial_home_score

            if initial_home_score > initial_away_score and int(post_match_form.home_team_score.data) < int(post_match_form.away_team_score.data):
                match.home_team_info.matches_won -= 1
                match.away_team_info.matches_lost -= 1

                match.away_team_info.matches_won += 1
                match.home_team_info.matches_lost += 1

            elif initial_home_score < initial_away_score and int(post_match_form.home_team_score.data) > int(post_match_form.away_team_score.data):
                match.away_team_info.matches_won -= 1
                match.home_team_info.matches_lost -= 1

                match.home_team_info.matches_won += 1
                match.away_team_info.matches_lost += 1

            elif initial_home_score > initial_away_score and int(post_match_form.home_team_score.data) == int(post_match_form.away_team_score.data):
                match.home_team_info.matches_won -= 1
                match.away_team_info.matches_lost -= 1

                match.home_team_info.matches_tied += 1
                match.away_team_info.matches_tied += 1

            elif initial_home_score < initial_away_score and int(post_match_form.home_team_score.data) == int(post_match_form.away_team_score.data):
                match.away_team_info.matches_won -= 1
                match.home_team_info.matches_lost -= 1

                match.home_team_info.matches_tied += 1
                match.away_team_info.matches_tied += 1

            elif initial_home_score == initial_away_score and int(post_match_form.home_team_score.data) < int(post_match_form.away_team_score.data):
                match.away_team_info.matches_tied -= 1
                match.home_team_info.matches_tied -= 1

                match.home_team_info.matches_lost += 1
                match.away_team_info.matches_won += 1

            elif initial_home_score == initial_away_score and int(post_match_form.home_team_score.data) > int(
                    post_match_form.away_team_score.data):
                match.away_team_info.matches_tied -= 1
                match.home_team_info.matches_tied -= 1

                match.away_team_info.matches_lost += 1
                match.home_team_info.matches_won += 1


        match.away_team_score = post_match_form.away_team_score.data
        match.home_team_score = post_match_form.home_team_score.data

        match.home_team_info.goals_for += int(post_match_form.home_team_score.data)
        match.home_team_info.goals_against += int(post_match_form.away_team_score.data)

        match.away_team_info.goals_for += int(post_match_form.away_team_score.data)
        match.away_team_info.goals_against += int(post_match_form.home_team_score.data)

        match.been_played = True

        flash('Scores successfully submitted!', 'success')

        db.session.commit()

        return redirect(url_for('matches.schedule', league_id=league.id))

    if highlights_link_form.validate_on_submit():
        match.highlights_link = highlights_link_form.highlights_link.data

        flash('Highlights link successfully submitted!', 'success')

        db.session.commit()


    return render_template('match_info.html', league=league, match=match, teams=teams, pre_match_form=pre_match_form, post_match_form=post_match_form, highlights_link_form=highlights_link_form)

