from app import app, db, admin_only, auto
from app.models import cfg_settings
from flask import abort, jsonify, request, Response
from flask.ext.login import login_required, current_user
from dateutil import parser
import json

@app.route('/ThreatKB/cfg_settings', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_all_cfg_settings():
    """Return all public config settings
    Return: list of config settings dictionaries"""
    entities = cfg_settings.Cfg_settings.query.filter_by(public=True).all()
    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype='application/json')


@app.route('/ThreatKB/cfg_settings/<key>', methods=['GET'])
@auto.doc()
def get_cfg_settings(key):
    """Return config settings associated with key if it is public
    Return: config settings dictionary"""
    entity = cfg_settings.Cfg_settings.query.get(key)

    if not entity or not entity.public:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/cfg_settings', methods=['POST'])
@auto.doc()
@login_required
@admin_only()
def create_cfg_settings():
    """Create config settings
    From Data: key (str), value (str), public (bool)
    Return: config setting dictionary"""
    entity = cfg_settings.Cfg_settings(
        key=request.json['key']
        , value=request.json['value']
        , description=request.json['description']
        , public=request.json.get('public', True),
    )
    db.session.add(entity)
    db.session.commit()

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/cfg_settings/<key>', methods=['PUT'])
@auto.doc()
@login_required
@admin_only()
def update_cfg_settings(key):
    """Update config setting associated with key
    From Data: key (str), value (str), public (bool)
    Return: config setting dictionary"""
    entity = cfg_settings.Cfg_settings.query.get(key)
    if not entity:
        abort(404)
    entity = cfg_settings.Cfg_settings(
        key=key,
        value=request.json['value'],
        description=request.json['description'],
        public=request.json.get('public', True),
    )
    db.session.merge(entity)
    db.session.commit()

    entity = cfg_settings.Cfg_settings.query.get(entity.key)

    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/cfg_settings/<key>', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_cfg_settings(key):
    """Delete config setting associated with key
    Return: None"""
    entity = cfg_settings.Cfg_settings.query.get(key)

    if not entity or not entity.public:
        abort(404)
    db.session.delete(entity)
    db.session.commit()

    return jsonify(''), 204
