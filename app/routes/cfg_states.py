from app import app, db, admin_only
from app.models import cfg_states
from flask import abort, jsonify, request
from flask.ext.login import login_required
import json


@app.route('/ThreatKB/cfg_states', methods=['GET'])
@login_required
def get_all_cfg_states():
    entities = cfg_states.Cfg_states.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/ThreatKB/cfg_states/<int:id>', methods=['GET'])
@login_required
@admin_only()
def get_cfg_states(id):
    entity = cfg_states.Cfg_states.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/cfg_states', methods=['POST'])
@login_required
@admin_only()
def create_cfg_states():
    entity = cfg_states.Cfg_states(
        state=request.json['state'],
        is_release_state=0 if not request.json.get("is_release_state", None) else 1
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/cfg_states/<int:id>', methods=['PUT'])
@login_required
@admin_only()
def update_cfg_states(id):
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
@login_required
@admin_only()
def delete_cfg_states(id):
    entity = cfg_states.Cfg_states.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
