from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
import logging
import os

app = Flask(__name__, static_url_path='')
app.secret_key = os.urandom(24)
app.config.from_object('config')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

from app.models import authentication
from app.models import c2ip
from app.models import c2dns
from app.models import yara_rule
from app.models import cfg_reference_text_templates
from app.models import cfg_states

from app.routes import index
from app.routes import authentication
from app.routes import c2ips
from app.routes import c2dns
from app.routes import yara_rules
from app.routes import cfg_reference_text_templates
from app.routes import cfg_states


@app.before_first_request
def setup_logging():
    app.logger.addHandler(logging.StreamHandler())
    app.logger.setLevel(logging.INFO)
