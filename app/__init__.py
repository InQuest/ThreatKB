from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
import logging

app = Flask(__name__, static_url_path='')
app.secret_key = "a" * 24  # os.urandom(24)
app.config.from_object('config')
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

bcrypt = Bcrypt(app)

app.config["SQLALCHEMY_ECHO"] = True

from app.models import authentication
from app.models import c2ip
from app.models import c2dns
from app.models import yara_rule
from app.models import cfg_reference_text_templates
from app.models import cfg_states
from app.models import comments
from app.models import authentication
from app.models import tags
from app.models import tags_mapping

from app.routes import index
from app.routes import authentication
from app.routes import c2ips
from app.routes import c2dns
from app.routes import yara_rules
from app.routes import cfg_reference_text_templates
from app.routes import cfg_states
from app.routes import comments
from app.routes import tags
from app.routes import tags_mapping


@app.before_first_request
def setup_logging():
    app.logger.addHandler(logging.StreamHandler())
    app.logger.setLevel(logging.DEBUG)


@login_manager.user_loader
def load_user(userid):
    app.logger.debug("load_user called with user_id: '%s'" % (str(userid)))
    return authentication.KBUser.query.get(int(userid))
