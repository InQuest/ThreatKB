import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))

# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
# SQLALCHEMY_DATABASE_URI = "mysql://username:password@host/db_name?use_unicode=1&charset=utf8"
SQLALCHEMY_TRACK_MODIFICATIONS = False

try:
    SQLALCHEMY_DATABASE_URI
except:
    sys.stderr.write("Did you forget to set SQLALCHEMY_DATABASE_URI? Quitting")
    sys.exit(1)

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
