import functools

from flask import Flask, abort
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from celery import Celery
import logging

from flask_login import current_user

app = Flask(__name__, static_url_path='')
app.secret_key = "a" * 24  # os.urandom(24)
app.config.from_object('config')


def make_celery(flask_app):
    celery_app = Celery(flask_app.import_name,
                        backend=flask_app.config['BROKER_URL'],
                        broker=flask_app.config['BROKER_URL'])
    celery_app.conf.update(flask_app.config)
    # task_base = celery_app.Task
    #
    # class ContextTask(task_base):
    #     abstract = True
    #
    #     def __call__(self, *args, **kwargs):
    #         with flask_app.app_context():
    #             return task_base.__call__(self, *args, **kwargs)
    #
    # celery_app.Task = ContextTask

    return celery_app


def admin_only():
    def wrapper(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.admin:
                return abort(403)
            return f(*args, **kwargs)
        return wrapped
    return wrapper


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
celery = make_celery(app)

app.config["SQLALCHEMY_ECHO"] = True

from app.models import users
from app.models import c2ip
from app.models import c2dns
from app.models import cfg_settings
from app.models import yara_rule
from app.models import cfg_reference_text_templates
from app.models import cfg_states
from app.models import comments
from app.models import users
from app.models import tags
from app.models import tags_mapping
from app.models import files
from app.models import cfg_category_range_mapping
from app.models import releases
from app.models import tasks

from app.routes import index
from app.routes import authentication
from app.routes import c2ips
from app.routes import c2dns
from app.routes import cfg_settings
from app.routes import yara_rules
from app.routes import cfg_reference_text_templates
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


@app.before_first_request
def setup_logging():
    app.logger.addHandler(logging.StreamHandler())
    app.logger.setLevel(logging.DEBUG)


@login_manager.user_loader
def load_user(userid):
    app.logger.debug("load_user called with user_id: '%s'" % (str(userid)))
    return users.KBUser.query.get(int(userid))
