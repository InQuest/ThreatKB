#!flask/bin/python
import sys
from flask.ext import bcrypt
from flask import Flask

app = Flask(__name__, static_url_path="")
b = bcrypt.Bcrypt(app)

print(b.generate_password_hash(sys.argv[1]))
