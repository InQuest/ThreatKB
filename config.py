import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))

# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_DATABASE_URI = "mysql://root:98supratt@192.168.56.103/inquestkb?use_unicode=1&charset=utf8"

try:
    SQLALCHEMY_DATABASE_URI
except:
    sys.stderr.write("Did you forget to set SQLALCHEMY_DATABASE_URI? Quitting")
    sys.exit(1)

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
