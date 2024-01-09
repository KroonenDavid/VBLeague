from itertools import combinations
from collections import defaultdict

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
            match = (teams[idx], teams[-idx - 1])
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