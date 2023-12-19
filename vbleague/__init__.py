from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5
from flask_mail import Mail
from vbleague.config import Config

db = SQLAlchemy()
mail = Mail()
bootstrap = Bootstrap5()

login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)


    from vbleague.users.routes import users
    from vbleague.leagues.routes import leagues
    from vbleague.teams.routes import teams
    from vbleague.main.routes import main
    from vbleague.errors.handlers import errors

    app.register_blueprint(users)
    app.register_blueprint(leagues)
    app.register_blueprint(teams)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    return app



