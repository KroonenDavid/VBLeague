from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    return render_template('index.html')


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