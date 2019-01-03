#!flask/bin/python
import sys
from flask_bcrypt import Bcrypt
from flask import Flask

app = Flask(__name__, static_url_path="")
b = Bcrypt(app)

print(b.generate_password_hash(sys.argv[1]))
