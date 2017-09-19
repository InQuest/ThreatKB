import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = "mysql://USERNAME:PASSWORD@DB_HOST/DB_NAME?use_unicode=1&charset=utf8"
SQLALCHEMY_TRACK_MODIFICATIONS = False

try:
    SQLALCHEMY_DATABASE_URI
except:
    sys.stderr.write("Did you forget to set SQLALCHEMY_DATABASE_URI? Quitting")
    sys.exit(1)
