from app import app, db, auto, admin_only, ENTITY_MAPPING
from app.models import metadata
from flask import abort, jsonify, request, Response
from flask.ext.login import login_required, current_user
import json


@app.route('/ThreatKB/metadata', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_all_metadata():
    """Return all active metadata
    Return: list of metadata dictionaries"""
    active_only = request.args.get("active_only", True)
    return Response(
        json.dumps([entity.to_dict() for entity in metadata.Metadata.query.filter_by(active=active_only).all()]),
        mimetype='application/json')


@app.route('/ThreatKB/metadata/<int:id>', methods=['GET'])
@login_required
@admin_only()
@auto.doc()
def get_metadata(id):
    """Return task associated with given id
    Return: task dictionary"""
    entity = metadata.Metadata.query.get(id)
    if not entity:
        abort(404)

    return jsonify(entity.to_dict())


@app.route('/ThreatKB/metadata', methods=['POST'])
@auto.doc()
@login_required
@admin_only()
def create_metadata():
    """Create new metadata
    From Data: key (str), active (int), artifact_type (int), type (str), default (str), show_in_table (int)
    Return: task dictionary"""
    entity = metadata.Metadata(
        key=request.json['key']
        , active=request.json.get('active', 1)
        , artifact_type=request.json['artifact_type']
        , type_=request.json['type']
        , default=request.json.get('default', None)
        , show_in_table=request.json.get('show_in_table', 0)
        , created_user_id=current_user.id
    )
    db.session.add(entity)
    db.session.commit()

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/metadata', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_metadata_by_id_in_param():
    """Delete metadata associated with the given id
    Return: None"""
    id = request.args.get("id")
    entity = metadata.Metadata.query.get(id)

    if not entity:
        abort(404)

    entity.active = False
    db.session.add(entity)
    db.session.commit()

    return jsonify(''), 204


@app.route('/ThreatKB/metadata/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_metadata(id):
    """Delete metadata associated with the given id
    Return: None"""
    entity = metadata.Metadata.query.get(id)

    if not entity:
        abort(404)

    # db.session.delete(entity)
    entity.active = False
    db.session.add(entity)
    db.session.commit()

    return jsonify(''), 204
