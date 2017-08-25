import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))

# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
# SQLALCHEMY_DATABASE_URI = "mysql://username:password@host/db_name?use_unicode=1&charset=utf8"
SQLALCHEMY_DATABASE_URI = "mysql://root:dc145236@localhost/inquestkb?use_unicode=1&charset=utf8"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# BROKER_URL = 'redis://:password@hostname:port/db_number0'
BROKER_URL = 'redis://localhost:6379/0'
# BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}

TASK_SERIALIZER = 'json'
RESULT_SERIALIZER = 'json'
ACCEPT_CONTENT = ['json']

FILE_STORE_PATH = "/tmp"
MAX_MILLIS_PER_FILE_THRESHOLD = 3.0

try:
    SQLALCHEMY_DATABASE_URI
except:
    sys.stderr.write("Did you forget to set SQLALCHEMY_DATABASE_URI? Quitting")
    sys.exit(1)
