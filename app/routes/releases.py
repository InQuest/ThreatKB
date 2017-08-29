import os

from dateutil import parser
from flask import abort, jsonify, request, send_file, json
from flask.ext.login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from app.models import releases


@app.route('/InquestKB/releases', methods=['GET'])
@login_required
def get_all_releases():
    entities = releases.Release.query.filter_by().all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/releases/<int:release_id>', methods=['GET'])
@login_required
def get_release(release_id):
    entity = releases.Release.query.get(release_id)

    if not entity:
        abort(404)

    return json.dumps(entity)


@app.route('/InquestKB/releases/<int:release_id>/release_notes', methods=['GET'])
@login_required
def get_release_notes(release_id):
    entity = releases.Release.query.get(release_id)

    if not entity:
        abort(404)

    return entity.generate_release_notes()


@app.route('/InquestKB/releases/<int:release_id>/signature_export', methods=['GET'])
@login_required
def get_release_notes(release_id):
    entity = releases.Release.query.get(release_id)

    if not entity:
        abort(404)

    return entity.generate_signature_export()


@app.route('/InquestKB/releases', methods=['POST'])
@login_required
def create_release():
    release = releases.Releases(
        name=request.json.get("name", None),
        date_start=parser.parse(request.json["date_start"]),
        state_dns=request.json["state_dns"],
        state_ip=request.json["state_ip"],
        state_yara_rule=request.json["state_yara_rule"],
        created_user_id=current_user.id
    )

    if request.json.get("date_end", None):
        release.date_end = parser.parse(request.json["date_end"])

    release.release_data = releases.Release.get_release_data()

    return jsonify(release)


@app.route('/InquestKB/releases/<int:release_id>', methods=['DELETE'])
@login_required
def delete_release(release_id):
    entity = releases.Release.query.get(release_id)
    if not entity:
        abort(404)

    db.session.delete(entity)
    db.session.commit()
    return '', 204
