import os
import sys

from flask_bcrypt import Bcrypt
from flask import Flask

SQL_PROTOCOL = os.getenv('SQL_PROTOCOL', 'mysql')
SQL_HOST = os.getenv('SQL_HOST', '127.0.0.1')
SQL_PORT = os.getenv('SQL_PORT', '3306')
SQL_DATABASE = os.getenv('SQL_DATABASE', 'threatkb_test')
SQL_USERNAME = os.getenv('SQL_USERNAME', 'root')
SQL_PASSWORD = os.getenv('SQL_PASSWORD', 'yourpassword')
SQLALCHEMY_DATABASE_URI = '{protocol}://{username}:{password}@{hostname}:{port}/{database}?use_unicode=1&charset=utf8'.format(
    protocol = SQL_PROTOCOL,
    username = SQL_USERNAME,
    password = SQL_PASSWORD,
    hostname = SQL_HOST,
    port = SQL_PORT,
    database = SQL_DATABASE
)

SQLALCHEMY_TRACK_MODIFICATIONS = False

# Dummy user for tests.
TEST_USER = 'admin'
TEST_PASSWORD = 'password'

app = Flask(__name__, static_url_path="")
b = Bcrypt(app)
TEST_PASSWORD_HASHED = b.generate_password_hash(TEST_PASSWORD)


try:
    SQLALCHEMY_DATABASE_URI
except:
    sys.stderr.write("Did you forget to set SQLALCHEMY_DATABASE_URI? Quitting")
    sys.exit(1)
