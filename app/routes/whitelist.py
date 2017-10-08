from flask_login import current_user

from app import app, db, admin_only, auto
from app.models import whitelist
from flask import abort, jsonify, request
from flask.ext.login import login_required
import json


@app.route('/ThreatKB/whitelist', methods=['GET'])
@auto.doc()
@login_required
def get_all_whitelist():
    """Return all whitelist
    Return: list of whitelist dictionaries"""
    entities = whitelist.Whitelist.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/ThreatKB/whitelist/<int:id>', methods=['GET'])
@auto.doc()
@login_required
def get_whitelist(id):
    """Return whitelist associated with given id
    Return: whitelist dictionary"""
    entity = whitelist.Whitelist.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/whitelist', methods=['POST'])
@auto.doc()
@login_required
def create_whitelist():
    """Create new whitelist
    From Data: whitelist_artifact(str), notes (str)
    Return: whitelist dictionary"""
    entity = whitelist.Whitelist(
        whitelist_artifact=request.json['whitelist_artifact'],
        notes=request.json['notes'],
        created_by_user_id=current_user.id,
        modified_by_user_id=current_user.id
    )
    db.session.add(entity)
    db.session.commit()

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/whitelist/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
def update_whitelist(id):
    """Update tag associated with given id
    From Data: whitelist_artifact(str), notes (str)
    Return: whitelist dictionary"""
    entity = whitelist.Whitelist.query.get(id)
    if not entity:
        abort(404)
    entity = whitelist.Whitelist(
        whitelist_artifact=request.json['whitelist_artifact'],
        notes=request.json['notes'],
        modified_by_user_id=current_user.id,
        id=id
    )
    db.session.merge(entity)
    db.session.commit()

    entity = whitelist.Whitelist.query.get(id)
    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/whitelist/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
def delete_whitelist(id):
    """Delete whitelist associated with given id
    Return: None"""
    entity = whitelist.Whitelist.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
