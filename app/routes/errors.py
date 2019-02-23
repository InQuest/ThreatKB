from flask import abort, jsonify, request, send_file, json, Response
from flask_login import login_required, current_user
from app import app, db, admin_only, auto
from app.models import errors


@app.route('/ThreatKB/errors', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_all_errors():
    """Return all releases in ThreatKB
    Return: list of release dictionaries"""
    entities = errors.Error.query.order_by(errors.Error.id.desc()).limit(50).all()
    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype="application/json")


@app.route('/ThreatKB/errors/<int:error_id>', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_error(error_id):
    """Return error associated with error_id
    Return: error dictionary"""
    entity = errors.Error.query.get(error_id)

    if not entity:
        abort(404)

    return Response(json.dumps(entity.to_dict()), mimetype="application/json")
