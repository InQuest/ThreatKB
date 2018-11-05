import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))

SQL_PROTOCOL = os.getenv('SQL_PROTOCOL', 'mysql')
SQL_HOST = os.getenv('SQL_HOST', '192.168.56.103')
SQL_PORT = os.getenv('SQL_PORT', '3306')
SQL_DATABASE = "threatkb_alpha_10312018"
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
#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

SQLALCHEMY_TRACK_MODIFICATIONS = False


try:
    SQLALCHEMY_DATABASE_URI
except:
    sys.stderr.write("Did you forget to set SQLALCHEMY_DATABASE_URI? Quitting")
    sys.exit(1)
