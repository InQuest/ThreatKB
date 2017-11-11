from app import app, db, admin_only, auto, current_user
from app.models import cfg_states
from flask import abort, jsonify, request, Response
from flask.ext.login import login_required
import json


@app.route('/ThreatKB/cfg_states', methods=['GET'])
@auto.doc()
@login_required
def get_all_cfg_states():
    """Return all config states
    Return: list of config state dictionaries"""
    entities = cfg_states.Cfg_states.query
    if not current_user.admin:
        entities = entities.filter_by(is_release_state=0)

    return Response(json.dumps([entity.to_dict() for entity in entities.all()]), mimetype='application/json')


@app.route('/ThreatKB/cfg_states/<int:id>', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_cfg_states(id):
    """Return config state associated with given id
    Return: config state dictionary"""
    entity = cfg_states.Cfg_states.query.get(id)
    if not entity:
        abort(404)

    if not current_user.admin and entity.is_release_state:
        abort(403)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/cfg_states', methods=['POST'])
@auto.doc()
@login_required
@admin_only()
def create_cfg_states():
    """Create config state
    From Data: state (str), is_release_state (bool)
    Return: config state dictionary
    """
    entity = cfg_states.Cfg_states(
        state=request.json['state'],
        is_release_state=0 if not request.json.get("is_release_state", None) else 1
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/cfg_states/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
@admin_only()
def update_cfg_states(id):
    """Update config state associated with the given id
    From Data: state (str), is_release_state (bool)
    Return: config setting dictionary"""
    entity = cfg_states.Cfg_states.query.get(id)
    if not entity:
        abort(404)
    entity = cfg_states.Cfg_states(
        state=request.json['state'],
        id=id,
        is_release_state=0 if not request.json.get("is_release_state", None) else 1
    )
    db.session.merge(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/cfg_states/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_cfg_states(id):
    """Delete config state associated with the given id
    Return: None"""
    entity = cfg_states.Cfg_states.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return jsonify(''), 204
