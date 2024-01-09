from flask import Blueprint, render_template
from vbleague.models import League

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    leagues = League.query.order_by(League.name).all()
    return render_template('index.html')