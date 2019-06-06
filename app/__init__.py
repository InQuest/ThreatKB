import functools

from flask import Flask, abort, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_login import current_user
from flask_migrate import Migrate
from flask import make_response
from functools import wraps, update_wrapper
from flask_caching import Cache
from flask_selfdoc import Autodoc
import datetime
import logging
import os
import distutils


app = Flask(__name__, static_url_path='')
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
app.secret_key = "a" * 24  # os.urandom(24)
app.config.from_object("config")

auto = Autodoc(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
celery = None

ENTITY_MAPPING = {"SIGNATURE": 1, "DNS": 2, "IP": 3, "TASK": 4, "RELEASE": 5}
ENTITY_MAPPING = {"SIGNATURE": 1, "DNS": 2, "IP": 3, "TASK": 4, "RELEASE": 5}
ACTIVITY_TYPE = {"ARTIFACT_CREATED": "Artifact Created",
                 "ARTIFACT_MODIFIED": "Artifact Modified",
                 "COMMENTS": 'Comment',
                 "STATE_TOGGLED": 'State Toggled',
                 "RELEASES_MADE": 'Release Made'}


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        import datetime as datetime
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


from app.models import cfg_settings


def set_celery_stuff(flask_app):
    flask_app.config["BROKER_URL"] = os.getenv("REDIS_BROKER_URL",
                                               cfg_settings.Cfg_settings.get_setting("REDIS_BROKER_URL"))
    flask_app.config["TASK_SERIALIZER"] = os.getenv("REDIS_TASK_SERIALIZER",
                                                    cfg_settings.Cfg_settings.get_setting("REDIS_TASK_SERIALIZER"))
    flask_app.config["RESULT_SERIALIZER"] = os.getenv("REDIS_RESULT_SERIALIZER",
                                                      cfg_settings.Cfg_settings.get_setting("REDIS_RESULT_SERIALIZER"))
    flask_app.config["ACCEPT_CONTENT"] = os.getenv("REDIS_ACCEPT_CONTENT",
                                                   cfg_settings.Cfg_settings.get_setting("REDIS_ACCEPT_CONTENT"))
    flask_app.config["FILE_STORE_PATH"] = os.getenv("FILE_STORE_PATH",
                                                    cfg_settings.Cfg_settings.get_setting("FILE_STORE_PATH"))
    flask_app.config["MAX_MILLIS_PER_FILE_THRESHOLD"] = os.getenv("MAX_MILLIS_PER_FILE_THRESHOLD",
                                                                  cfg_settings.Cfg_settings.get_setting(
                                                                      "MAX_MILLIS_PER_FILE_THRESHOLD"))

    if flask_app.config["MAX_MILLIS_PER_FILE_THRESHOLD"]:
        flask_app.config["MAX_MILLIS_PER_FILE_THRESHOLD"] = float(flask_app.config["MAX_MILLIS_PER_FILE_THRESHOLD"])

set_celery_stuff(app)

print("app config: %s" % (str(app.config)))

from app.celeryapp import make_celery

celery = make_celery(app)


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
from app.routes.activity_log import *
from app.routes.macros import *

from app.models import users
from app.models import c2ip
from app.models import c2dns
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
from app.models import activity_log
from app.models import macros

from app.geo_ip_helper import get_geo_for_ip


# DB functions below used by unit tests.
def connect_db():
    """Connects to the specific database."""
    rv = SQLAlchemy(app)
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    return connect_db()


def init_db():
    """Initializes the database."""
    db = get_db()
    migrate = Migrate(app, db)

    def upgrade(revision="head"):
        with app.app_context():
            from flask_migrate import upgrade as _upgrade
            _upgrade(revision=revision)

    upgrade()


def deinit_db():
    """Deinitializes the database."""
    db = get_db()
    migrate = Migrate(app, db)

    def downgrade(revision="base"):
        with app.app_context():
            from flask_migrate import downgrade as _downgrade
            _downgrade(revision=revision)

    downgrade()


@app.teardown_request
def teardown_request(exception):
    if exception:
        db.session.rollback()
    db.session.remove()


@app.before_first_request
def setup_logging():
    app.logger.addHandler(logging.StreamHandler())
    app.logger.setLevel(app.config["LOGGING_LEVEL"])


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
                abort(401)
        else:
            abort(401)

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
    from app.models import activity_log
    from app.models import macros

    set_celery_stuff(app)

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
    from app.routes import activity_log
    from app.routes import macros

    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

    @app.teardown_request
    def teardown_request(exception):
        if exception:
            db.session.rollback()
        db.session.remove()

    @app.before_first_request
    def setup_logging():
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(app.config["LOGGING_LEVEL"])

    @login_manager.user_loader
    @cache.memoize(timeout=60)
    def load_user(userid):
        app.logger.debug("load_user called with user_id: '%s'" % (str(userid)))
        return users.KBUser.query.get(int(userid))

    @login_manager.request_loader
    @cache.memoize(timeout=60)
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
                    abort(401)
            else:
                abort(401)

        return None


def run(debug=False, port=0, host=''):
    import os
    port = port or int(os.getenv('LISTEN_PORT', 5000))
    host = host or os.getenv('LISTEN_ON', '127.0.0.1')
    debug = debug or os.getenv("DEBUG", False)

    generate_app()
    app.run(debug=debug, port=port, host=host)
