# coding=utf-8
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown
from config import config
from flask_uploads import configure_uploads, UploadSet, SCRIPTS

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()
files = UploadSet('codefiles', SCRIPTS)

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    configure_uploads(app, files)

    from .bp_topulogy import topulogy as main_blueprint
    app.register_blueprint(main_blueprint)

    from .bp_auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .bp_ssh import bp_ssh as ssh_blueprint
    app.register_blueprint(ssh_blueprint, url_prefix='/bp_ssh')

    return app
