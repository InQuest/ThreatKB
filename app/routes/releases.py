from flask import abort, jsonify, request, send_file, json, Response
from flask.ext.login import login_required, current_user
from app import app, db, admin_only
from app.models import releases

import tempfile
import uuid


@app.route('/ThreatKB/releases', methods=['GET'])
@login_required
@admin_only()
def get_all_releases():
    entities = releases.Release.query.filter_by().all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/ThreatKB/releases/<int:release_id>', methods=['GET'])
@login_required
@admin_only()
def get_release(release_id):
    entity = releases.Release.query.get(release_id)

    if not entity:
        abort(404)

    return json.dumps(entity)


@app.route('/ThreatKB/releases/<int:release_id>/release_notes', methods=['GET'])
@login_required
@admin_only()
def generate_release_notes(release_id):
    entity = releases.Release.query.get(release_id)

    if not entity:
        abort(404)

    filename = str(release_id) + "_release_notes.txt"
    content = entity.generate_release_notes()
    content.seek(0)
    tfile = "%s/%s" % (tempfile.gettempdir(), str(uuid.uuid4()).replace("-", ""))
    with open(tfile, "w") as t:
        t.write(content.read())
    return send_file(tfile, attachment_filename=filename, mimetype="text/plain", as_attachment=True)


@app.route('/ThreatKB/releases/<int:release_id>/artifact_export', methods=['GET'])
@login_required
@admin_only()
def generate_artifact_export(release_id):
    entity = releases.Release.query.get(release_id)

    if not entity:
        abort(404)

    filename = str(release_id) + "_release.zip"
    content = entity.generate_artifact_export()
    content.seek(0)

    tfile = "%s/%s" % (tempfile.gettempdir(), str(uuid.uuid4()).replace("-", ""))
    with open(tfile, "w") as t:
        t.write(content.read())
    return send_file(tfile, attachment_filename=filename, as_attachment=True)


@app.route('/ThreatKB/releases', methods=['POST'])
@login_required
@admin_only()
def create_release():
    release = releases.Release(
        name=request.json.get("name", None),
        is_test_release=request.json.get("is_test_release", 0),
        created_user_id=current_user.id
    )

    release.release_data = release.get_release_data()
    release.created_user = current_user
    db.session.merge(release)
    db.session.commit()

    release = releases.Release.query.filter(release.id).first()
    return jsonify(release.to_dict())


@app.route('/ThreatKB/releases/<int:release_id>', methods=['DELETE'])
@login_required
@admin_only()
def delete_release(release_id):
    entity = releases.Release.query.get(release_id)
    if not entity:
        abort(404)

    db.session.delete(entity)
    db.session.commit()
    return '', 204
