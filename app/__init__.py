import functools

from flask import Flask, abort, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask_login import current_user
from flask import make_response
from functools import wraps, update_wrapper
from flask.ext.autodoc import Autodoc
import datetime
import logging
import os
import distutils


app = Flask(__name__, static_url_path='')
app.secret_key = "a" * 24  # os.urandom(24)
app.config.from_object("config")

auto = Autodoc(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
celery = None

app.config["SQLALCHEMY_ECHO"] = distutils.util.strtobool(os.getenv("SQLALCHEMY_ECHO", "1"))

ENTITY_MAPPING = {"SIGNATURE": 1, "DNS": 2, "IP": 3, "TASK": 4}


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


def admin_only():
    def wrapper(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.admin:
                return abort(403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper


from app.routes.version import *
from app.routes.index import *
from app.routes.authentication import *
from app.routes.c2ips import *
from app.routes.c2dns import *
from app.routes.cfg_settings import *
from app.routes.yara_rules import *
from app.routes.cfg_states import *
from app.routes.comments import *
from app.routes.tags import *
from app.routes.tags_mapping import *
from app.routes.files import *
from app.routes.import_ import *
from app.routes.cfg_category_range_mapping import *
from app.routes.test_yara_rule import *
from app.routes.error_handling import *
from app.routes.releases import *
from app.routes.tasks import *
from app.routes.documentation import *
from app.routes.access_keys import *
from app.routes.whitelist import *
from app.routes.search import *
from app.routes.bookmarks import *
from app.routes.scripts import *
from app.routes.metadata import *
from app.routes.errors import *

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
from app.models import metadata
from app.models import errors


app.config["BROKER_URL"] = Cfg_settings.get_private_setting("REDIS_BROKER_URL")
app.config["TASK_SERIALIZER"] = Cfg_settings.get_private_setting("REDIS_TASK_SERIALIZER")
app.config["RESULT_SERIALIZER"] = Cfg_settings.get_private_setting("REDIS_RESULT_SERIALIZER")
app.config["ACCEPT_CONTENT"] = Cfg_settings.get_private_setting("REDIS_ACCEPT_CONTENT")
app.config["FILE_STORE_PATH"] = Cfg_settings.get_private_setting("FILE_STORE_PATH")
app.config["MAX_MILLIS_PER_FILE_THRESHOLD"] = Cfg_settings.get_private_setting(
    "MAX_MILLIS_PER_FILE_THRESHOLD")

if app.config["MAX_MILLIS_PER_FILE_THRESHOLD"]:
    app.config["MAX_MILLIS_PER_FILE_THRESHOLD"] = float(app.config["MAX_MILLIS_PER_FILE_THRESHOLD"])

from app.celeryapp import make_celery
celery = make_celery(app)

from app.geo_ip_helper import get_geo_for_ip


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
        valid_token = is_token_active(token)
        if valid_token:
            user = users.KBUser.verify_auth_token(str(token), s_key)
            if user:
                return user
            else:
                abort(403)
        else:
            abort(403)

    return None


def generate_app():

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
    from app.models import metadata
    from app.models import errors

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
    from app.routes import metadata
    from app.routes import errors

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


def run(debug=False, port=0, host=''):
    import os
    port = port or int(os.getenv('LISTEN_PORT', 5000))
    host = host or os.getenv('LISTEN_ON', '127.0.0.1')
    debug = debug or os.getenv("DEBUG", False)

    generate_app()
    app.run(debug=debug, port=port, host=host)
