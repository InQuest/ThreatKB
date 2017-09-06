from app import app, db, admin_only
from app.models import cfg_settings
from flask import abort, jsonify, request
from flask.ext.login import login_required, current_user
from dateutil import parser
import json


@app.route('/ThreatKB/cfg_settings', methods=['GET'])
@login_required
@admin_only()
def get_all_cfg_settings():
    entities = cfg_settings.Cfg_settings.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/ThreatKB/cfg_settings/<key>', methods=['GET'])
def get_cfg_settings(key):
    entity = cfg_settings.Cfg_settings.query.get(key)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/cfg_settings', methods=['POST'])
@login_required
@admin_only()
def create_cfg_settings():
    entity = cfg_settings.Cfg_settings(
        key=request.json['key']
        , value=request.json['value']
    )
    db.session.add(entity)
    db.session.commit()

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/cfg_settings/<key>', methods=['PUT'])
@login_required
@admin_only()
def update_cfg_settings(key):
    entity = cfg_settings.Cfg_settings.query.get(key)
    if not entity:
        abort(404)
    entity = cfg_settings.Cfg_settings(
        key=key,
        value=request.json['value'],
        public=request.json.get('public', False),
    )
    db.session.merge(entity)
    db.session.commit()

    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/cfg_settings/<key>', methods=['DELETE'])
@login_required
@admin_only()
def delete_cfg_settings(key):
    entity = cfg_settings.Cfg_settings.query.get(key)

    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()

    return '', 204
