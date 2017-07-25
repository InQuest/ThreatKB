from app import app, db
from app.models import cfg_states
from flask import abort, jsonify, request
import datetime
import json


@app.route('/InquestKB/cfg_states', methods=['GET'])
def get_all_cfg_states():
    entities = cfg_states.Cfg_states.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/cfg_states/<int:id>', methods=['GET'])
def get_cfg_states(id):
    entity = cfg_states.Cfg_states.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/InquestKB/cfg_states', methods=['POST'])
def create_cfg_states():
    entity = cfg_states.Cfg_states(
        state=request.json['state']
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/InquestKB/cfg_states/<int:id>', methods=['PUT'])
def update_cfg_states(id):
    entity = cfg_states.Cfg_states.query.get(id)
    if not entity:
        abort(404)
    entity = cfg_states.Cfg_states(
        state=request.json['state'],
        id=id
    )
    db.session.merge(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 200


@app.route('/InquestKB/cfg_states/<int:id>', methods=['DELETE'])
def delete_cfg_states(id):
    entity = cfg_states.Cfg_states.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
