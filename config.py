import os
import sys
import logging
from distutils import util

basedir = os.path.abspath(os.path.dirname(__file__))

SQL_PROTOCOL = os.getenv('SQL_PROTOCOL', 'mysql')
SQL_HOST = os.getenv('SQL_HOST', '127.0.0.1')
SQL_PORT = os.getenv('SQL_PORT', '3306')
# SQL_DATABASE = os.getenv('SQL_DATABASE', 'inquest_test')
SQL_DATABASE = os.getenv('SQL_DATABASE', 'tkb_1312019')
SQL_USERNAME = os.getenv('SQL_USERNAME', 'root')
SQL_PASSWORD = os.getenv('SQL_PASSWORD', '98supratt')
SQLALCHEMY_DATABASE_URI = '{protocol}://{username}:{password}@{hostname}:{port}/{database}?use_unicode=1&charset=utf8'.format(
    protocol = SQL_PROTOCOL,
    username = SQL_USERNAME,
    password = SQL_PASSWORD,
    hostname = SQL_HOST,
    port = SQL_PORT,
    database = SQL_DATABASE
)

LOGGING_LEVEL = getattr(logging, os.getenv('LOGGING_LEVEL', 'DEBUG'))

SQLALCHEMY_ECHO = util.strtobool(os.getenv("SQLALCHEMY_ECHO", "1"))

# SQLALCHEMY_DATABASE_URI = "sqlite://"
# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

SQLALCHEMY_TRACK_MODIFICATIONS = False


try:
    SQLALCHEMY_DATABASE_URI
except:
    sys.stderr.write("Did you forget to set SQLALCHEMY_DATABASE_URI? Quitting")
    sys.exit(1)
