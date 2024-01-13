from flask import url_for, redirect, flash
from vbleague import db
from sqlalchemy import func, and_
from vbleague.models import Match

#MR GPT helped me write an automatic scheduling algorithm
def generate_schedule(matches_per_week, teams):
    if len(teams) % 2 != 0:
        teams.append("BYE")

    match_schedule = []
    num_weeks = len(teams) - 1

    for week in range(num_weeks):
        matches = []
        half = len(teams) // 2

        for idx in range(half):
            if week % 2 == 0:
                match = (teams[idx], teams[-idx - 1])
            else:
                match = (teams[-idx - 1], teams[idx])
            matches.append(match)

        match_schedule.append(matches)

        teams.insert(1, teams.pop())

    match_day_schedule = []
    week_matches = []

    for matches in match_schedule:
        for match in matches:
            week_matches.append(match)
            if len(week_matches) == matches_per_week:
                match_day_schedule.append(week_matches)
                week_matches = []

    if week_matches:
        match_day_schedule.append(week_matches)

    return match_day_schedule

def update_match_results(match, post_match_form):
    old_away_score = match.away_team_score
    old_home_score = match.home_team_score

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
        match.home_team_info.goals_for -= old_home_score
        match.home_team_info.goals_against -= old_away_score

        match.away_team_info.goals_for -= old_away_score
        match.away_team_info.goals_against -= old_home_score

        if old_home_score > old_away_score and int(post_match_form.home_team_score.data) < int(post_match_form.away_team_score.data):
            match.home_team_info.matches_won -= 1
            match.away_team_info.matches_lost -= 1

            match.away_team_info.matches_won += 1
            match.home_team_info.matches_lost += 1

        elif old_home_score < old_away_score and int(post_match_form.home_team_score.data) > int(post_match_form.away_team_score.data):
            match.away_team_info.matches_won -= 1
            match.home_team_info.matches_lost -= 1

            match.home_team_info.matches_won += 1
            match.away_team_info.matches_lost += 1

        elif old_home_score > old_away_score and int(post_match_form.home_team_score.data) == int(post_match_form.away_team_score.data):
            match.home_team_info.matches_won -= 1
            match.away_team_info.matches_lost -= 1

            match.home_team_info.matches_tied += 1
            match.away_team_info.matches_tied += 1

        elif old_home_score < old_away_score and int(post_match_form.home_team_score.data) == int(post_match_form.away_team_score.data):
            match.away_team_info.matches_won -= 1
            match.home_team_info.matches_lost -= 1

            match.home_team_info.matches_tied += 1
            match.away_team_info.matches_tied += 1

        elif old_home_score == old_away_score and int(post_match_form.home_team_score.data) < int(post_match_form.away_team_score.data):
            match.away_team_info.matches_tied -= 1
            match.home_team_info.matches_tied -= 1

            match.home_team_info.matches_lost += 1
            match.away_team_info.matches_won += 1

        elif old_home_score == old_away_score and int(post_match_form.home_team_score.data) > int(post_match_form.away_team_score.data):
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
