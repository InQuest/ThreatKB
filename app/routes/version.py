from flask import request, Response, json, abort
from flask.ext.login import login_required
from app import app, db, auto
import json


@app.route('/ThreatKB/version', methods=['GET'])
@auto.doc()
def get_version():
    """Returns the version of ThreatKB.
    Return: version number"""
    version = [v.strip() for v in open("version", "r").readlines()]
    return Response(json.dumps({"version": version[0], "version_email": version[1], "version_date": version[2][:-6]}),
                    mimetype='application/json')
