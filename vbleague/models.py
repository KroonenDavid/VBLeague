from vbleague import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship


team_membership = db.Table(
    'team_membership',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id'), primary_key=True)
)


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

    position = db.Column(db.String(100))
    matches_played = db.Column(db.Integer, nullable=False, default=0)
    goals_scored = db.Column(db.Integer, nullable=False, default=0)
    assists = db.Column(db.Integer, nullable=False, default=0)
    shot_percentage = db.Column(db.Integer, nullable=False, default=0)
    saves_made = db.Column(db.Integer, nullable=False, default=0)
    goals_against = db.Column(db.Integer, nullable=False, default=0)
    save_percentage = db.Column(db.Integer, nullable=False, default=0)
    profile_pic = db.Column(db.String(1000), nullable=False, default='Default_pfp.png')


class League(db.Model):
    __tablename__ = "leagues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=False, unique=True)
    location = db.Column(db.String(1000), nullable=False)
    days = db.Column(db.String(1000), nullable=False)
    division = db.Column(db.String(1000), nullable=False)
    team_size = db.Column(db.String(1000), nullable=False)
    maps_url = db.Column(db.String(1000), nullable=False)
    bio = db.Column(db.Text)

    teams = relationship("Team", back_populates="parent_league", cascade="all, delete-orphan")


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)

    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False)
    parent_league = relationship("League", back_populates="teams")

    name = db.Column(db.String(1000))
    matches_played = db.Column(db.Integer, nullable=False, default=0)
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
