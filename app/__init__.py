import functools

from flask import Flask, abort, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask_login import current_user
from flask.ext.autodoc import Autodoc
import logging

app = Flask(__name__, static_url_path='')
app.secret_key = "a" * 24  # os.urandom(24)
app.config.from_object("config")

auto = Autodoc(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
celery = None

app.config["SQLALCHEMY_ECHO"] = True


def admin_only():
    def wrapper(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.admin:
                return abort(403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper


def run(debug=False, port=5000, host='127.0.0.1'):
    global celery
    from app.models import users
    from app.models import c2ip
    from app.models import c2dns
    from app.models import cfg_settings
    from app.models import yara_rule
    from app.models import cfg_states
    from app.models import comments
    from app.models import tags
    from app.models import tags_mapping
    from app.models import files
    from app.models import scripts
    from app.models import cfg_category_range_mapping
    from app.models import releases
    from app.models import tasks
    from app.models import access_keys
    from app.models import users
    from app.models import whitelist
    from app.models import bookmarks

    app.config["BROKER_URL"] = cfg_settings.Cfg_settings.get_private_setting("REDIS_BROKER_URL")
    app.config["TASK_SERIALIZER"] = cfg_settings.Cfg_settings.get_private_setting("REDIS_TASK_SERIALIZER")
    app.config["RESULT_SERIALIZER"] = cfg_settings.Cfg_settings.get_private_setting("REDIS_RESULT_SERIALIZER")
    app.config["ACCEPT_CONTENT"] = cfg_settings.Cfg_settings.get_private_setting("REDIS_ACCEPT_CONTENT")
    app.config["FILE_STORE_PATH"] = cfg_settings.Cfg_settings.get_private_setting("FILE_STORE_PATH")
    app.config["MAX_MILLIS_PER_FILE_THRESHOLD"] = cfg_settings.Cfg_settings.get_private_setting(
        "MAX_MILLIS_PER_FILE_THRESHOLD")

    if app.config["MAX_MILLIS_PER_FILE_THRESHOLD"]:
        app.config["MAX_MILLIS_PER_FILE_THRESHOLD"] = float(app.config["MAX_MILLIS_PER_FILE_THRESHOLD"])

    from app.celeryapp import make_celery
    celery = make_celery(app)

    from app.geo_ip_helper import get_geo_for_ip

    from app.routes import index
    from app.routes import authentication
    from app.routes import c2ips
    from app.routes import c2dns
    from app.routes import cfg_settings
    from app.routes import yara_rules
    from app.routes import cfg_states
    from app.routes import comments
    from app.routes import tags
    from app.routes import tags_mapping
    from app.routes import files
    from app.routes import import_
    from app.routes import cfg_category_range_mapping
    from app.routes import test_yara_rule
    from app.routes import error_handling
    from app.routes import releases
    from app.routes import tasks
    from app.routes import documentation
    from app.routes import access_keys
    from app.routes import whitelist
    from app.routes import search
    from app.routes import bookmarks
    from app.routes import version
    from app.routes import scripts

    @app.before_first_request
    def setup_logging():
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.DEBUG)

    @login_manager.user_loader
    def load_user(userid):
        app.logger.debug("load_user called with user_id: '%s'" % (str(userid)))
        return users.KBUser.query.get(int(userid))

    @login_manager.request_loader
    def load_user_from_request(request):
        token = request.args.get('token')
        s_key = str(request.args.get('secret_key'))
        if token and s_key:
            valid_token = access_keys.is_token_active(token)
            if valid_token:
                user = users.KBUser.verify_auth_token(str(token), s_key)
                if user:
                    return user
                else:
                    abort(403)
            else:
                abort(403)

        return None

    from app import app as APP
    APP.run(debug=debug, port=port, host=host)
