from app import app, db, auto
from app.models import macros
from flask import abort, jsonify, request, Response
from flask_login import login_required
import json


@app.route('/ThreatKB/macros', methods=['GET'])
@auto.doc()
@login_required
def get_all_macros():
    """Return all macros
    Return: list of macro dictionaries"""
    entities = macros.Macros.query.all()
    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype='application/json')


@app.route('/ThreatKB/macros/<tag>', methods=['GET'])
def get_macro(tag):
    """Return macro associated with tag
    Return: macro dictionary"""
    entity = macros.Macros.query.get(tag)

    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/macros', methods=['POST'])
@auto.doc()
@login_required
def create_macro():
    """Create macro
    From Data: tag (str), value (str)
    Return: macro dictionary"""
    entity = macros.Macros(
        tag=request.json['tag'],
        value=request.json['value']
    )
    db.session.add(entity)
    db.session.commit()

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/macros/<tag>', methods=['PUT'])
@auto.doc()
@login_required
def update_macro(tag):
    """Update macro associated with tag
    From Data: tag (str), value (str)
    Return: macro dictionary"""
    entity = macros.Macros.query.get(tag)
    if not entity:
        abort(404)
    entity = macros.Macros(
        tag=tag,
        value=request.json['value'],
    )
    db.session.merge(entity)
    db.session.commit()

    entity = macros.Macros.query.get(entity.tag)

    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/macros/<tag>', methods=['DELETE'])
@auto.doc()
@login_required
def delete_macro(tag):
    """Delete macro associated with tag
    Return: None"""
    entity = macros.Macros.query.get(tag)

    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()

    return jsonify(''), 204
