from flask import abort, jsonify, request, send_file, json, Response
from flask.ext.login import login_required, current_user
from app import app, db, admin_only, auto
from app.models import releases
import tempfile
import uuid


@app.route('/ThreatKB/releases', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_all_releases():
    """Return all releases in ThreatKB
    Return: list of release dictionaries"""
    entities = releases.Release.query.filter_by().all()
    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype="application/json")


@app.route('/ThreatKB/releases/<int:release_id>', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_release(release_id):
    """Return release associated with release_id
    Return: release dictionary"""
    entity = releases.Release.query.get(release_id)

    if not entity:
        abort(404)

    return Response(json.dumps(entity), mimetype="application/json")


@app.route('/ThreatKB/releases/latest', methods=['GET'])
@auto.doc()
@login_required
def get_release_latest():
    """Return the latest release data
    Return: release dictionary"""
    entity = releases.Release.query.filter(releases.Release.is_test_release == 0).order_by(
        releases.Release.id.desc()).first()

    if not entity:
        entity = {}
    elif current_user.admin:
        entity = entity.to_dict()
    else:
        entity = entity.to_small_dict()

    return Response(json.dumps(entity), mimetype="application/json")


@app.route('/ThreatKB/releases/<int:release_id>/release_notes', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def generate_release_notes(release_id):
    """Generate and return release notes for release associated with release_id
    Return: release text file"""
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
@auto.doc()
@login_required
@admin_only()
def generate_artifact_export(release_id):
    """Generate and return artifact export zip file for the release associated with release_id
    Return: release zip file with a single file for all IPs, single file for all DNS, and consolidated category yara files"""
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
@auto.doc()
@login_required
@admin_only()
def create_release():
    """Create new release
    From Data: name (str), is_test_release (bool)
    Return: release dictionary"""
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
@auto.doc()
@login_required
@admin_only()
def delete_release(release_id):
    """Delete release associated with release_id
    Return: None"""
    entity = releases.Release.query.get(release_id)
    if not entity:
        abort(404)

    db.session.delete(entity)
    db.session.commit()
    return jsonify(''), 204
