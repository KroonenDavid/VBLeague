from flask_login import UserMixin
from sqlalchemy.orm import relationship
from itsdangerous import URLSafeTimedSerializer as Serializer
from vbleague import login_manager, db
from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property



default_bio = ('<h1><strong>Day at 00:00am-00:00pm</strong></h1>'
               '<h1><span style="color:#e74c3c">Season start date: MM/DD/YYYY</span></h1>'
               '<p><strong>Field Location:</strong><a href="http://127.0.0.1:5000/leagues/4">&nbsp;Location (with link to field)</a></p>'
               '<p><strong>Team Size:</strong>&nbsp;11v11</p>'
               '<p><strong>Field Type:</strong>&nbsp;Turf/Grass/Artificial</p>'
               '<p><strong>Team minimum:</strong>&nbsp;11 players (3 Male or 3 Female).</p>'
               '<p><strong>Season Format:</strong>&nbsp;8 Weeks of Regular Season + Playoffs</p>')

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

#ADD STATS HERE
team_membership = db.Table(
    'team_membership',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id'), primary_key=True),
    db.Column('matches_played', db.Integer, default=0),
    db.Column('goals_scored', db.Integer, default=0),
    db.Column('assists', db.Integer, default=0),
    db.Column('saves_made', db.Integer, default=0),
    db.Column('goals_against', db.Integer, default=0),
)


#ALL STATS HERE SHOULD BE HYBRID PROPERTIES THAT ADD UP THE STATS ABOVE
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    birthdate = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    shirt_size = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(1000), nullable=False, default="No bio yet!")
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)

    position = db.Column(db.String(100))
    # matches_played = db.Column(db.Integer, nullable=False, default=0)
    goals_scored = db.Column(db.Integer, nullable=False, default=0)
    assists = db.Column(db.Integer, nullable=False, default=0)
    shot_percentage = db.Column(db.Integer, nullable=False, default=0)
    saves_made = db.Column(db.Integer, nullable=False, default=0)
    goals_against = db.Column(db.Integer, nullable=False, default=0)
    save_percentage = db.Column(db.Integer, nullable=False, default=0)
    profile_pic = db.Column(db.String(1000), nullable=False, default='Default_pfp.png')



    # @hybrid_property
    # def save_percentage(self):
    #     try:
    #         (self.saves_made) / (self.goals_against) * 100
    #     except ZeroDivisionError:
    #         return 100
    #     else:
    #         return (self.saves_made) / (self.goals_against) * 100

    @hybrid_property
    def matches_played(self):
        teams = db.session.query(team_membership).filter_by(user_id=self.id).all()
        total = [stats.matches_played for stats in teams]
        return sum(total)



    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

class Match(db.Model):
    __tablename__ = "matches"
    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.Integer, db.ForeignKey('teams.id'), primary_key=True)
    home_team_score = db.Column(db.Integer, nullable=False, default=0)
    away_team = db.Column(db.Integer, db.ForeignKey('teams.id'), primary_key=True)
    away_team_score = db.Column(db.Integer, nullable=False, default=0)
    date = db.Column(db.String, nullable=False, default='TBD')
    field = db.Column(db.String, nullable=False, default='TBD')
    highlights_link = db.Column(db.String, nullable=False, default='TBD')

class League(db.Model):
    __tablename__ = "leagues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=False, unique=True)
    location = db.Column(db.String(1000), nullable=False)
    days = db.Column(db.String(1000), nullable=False)
    division = db.Column(db.String(1000), nullable=False)
    team_size = db.Column(db.String(1000), nullable=False)
    maps_url = db.Column(db.String(1000), nullable=False)
    bio = db.Column(db.Text, default=default_bio)

    teams = relationship("Team", back_populates="parent_league", cascade="all, delete-orphan")


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)

    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False)
    parent_league = relationship("League", back_populates="teams")

    name = db.Column(db.String(1000))
    matches_won = db.Column(db.Integer, nullable=False, default=0)
    matches_lost = db.Column(db.Integer, nullable=False, default=0)
    matches_tied = db.Column(db.Integer, nullable=False, default=0)
    goals_for = db.Column(db.Integer, nullable=False, default=0)
    goals_against = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.String(1000), nullable=False)
    logo = db.Column(db.String(1000))
    password = db.Column(db.String(1000), nullable=False)



    captain_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    captain = relationship("User", foreign_keys=[captain_id])

    players = relationship("User", secondary=team_membership, backref="teams_joined")

    @hybrid_property
    def points(self):
        return (self.matches_won*3) + (self.matches_tied)

    @hybrid_property
    def goal_difference(self):
        return (self.goals_for - self.goals_against)

    @hybrid_property
    def matches_played(self):
        return (self.matches_won + self.matches_tied + self.matches_lost)

    def __repr__(self):
        return f'{self.name}'


    def generate_join_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'team_id': self.id})

    @staticmethod
    def verify_join_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            team_id = s.loads(token, max_age=expires_sec)['team_id']
        except:
            return None
        return Team.query.get(team_id)

