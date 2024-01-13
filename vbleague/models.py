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
)

match_membership = db.Table(
    'match_membership',
    db.Column('match_id', db.Integer, db.ForeignKey('matches.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id'), nullable=False),
)

class PlayerStats(db.Model):
    __tablename__ = "player_stats"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    match_played = db.Column(db.Boolean, default=False)
    goals_scored = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    saves_made = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)

    match = relationship('Match', back_populates='player_stats')
    team = relationship('Team', back_populates='stats')
    user = relationship('User', back_populates='stats')

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
    profile_pic = db.Column(db.String(1000), nullable=False, default='Default_pfp.png')

    teams = relationship("Team", secondary=team_membership, backref="team_players")
    stats = relationship('PlayerStats', back_populates='user')

    # @hybrid_property
    # def matches_played(self):
    #     return sum(stat.matches_played for stat in self.player_team_stats)
    #
    # @hybrid_property
    # def goals_scored(self):
    #     return sum(stat.goals_scored for stat in self.player_team_stats)
    #
    # @hybrid_property
    # def assists(self):
    #     return sum(stat.assists for stat in self.player_team_stats)
    #
    # @hybrid_property
    # def save_percentage(self):
    #     try:
    #         return (self.saves_made) / (self.goals_against) * 100
    #     except ZeroDivisionError:
    #         return 100

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

    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'))
    home_team = db.Column(db.Integer, db.ForeignKey('teams.id'))
    home_team_score = db.Column(db.Integer, nullable=False, default=0)
    away_team = db.Column(db.Integer, db.ForeignKey('teams.id'))
    away_team_score = db.Column(db.Integer, nullable=False, default=0)
    date = db.Column(db.String, nullable=False, default='TBD')
    time = db.Column(db.String, nullable=False, default='TBD')
    field = db.Column(db.String, nullable=False, default='TBD')
    week = db.Column(db.Integer, nullable=False, default=0)
    highlights_link = db.Column(db.String, nullable=False, default='TBD')
    been_played = db.Column(db.Boolean, nullable=False, default=0)

    home_team_info = relationship('Team', foreign_keys=[home_team])
    away_team_info = relationship('Team', foreign_keys=[away_team])

    teams = relationship('Team', secondary='match_membership', back_populates='matches')
    player_stats = relationship('PlayerStats', back_populates='match')



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

    players = relationship("User", secondary=team_membership, backref="team_players")
    stats = relationship('PlayerStats', back_populates='team')
    matches = relationship('Match', secondary='match_membership', back_populates="teams")

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

