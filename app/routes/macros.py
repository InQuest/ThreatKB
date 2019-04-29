from app import app, db, auto
from app.models import macros
from flask import abort, jsonify, request, Response
from flask_login import login_required, current_user
import json


@app.route('/ThreatKB/macros', methods=['GET'])
@auto.doc()
@login_required
def get_all_macros():
    """Return all macros
    Return: list of macro dictionaries"""

    view = request.args.get("view", "Active Only")

    if view == "All":
        include_inactive = True
        include_active = True
    elif view == "Active Only":
        include_inactive = False
        include_active = True
    elif view == "Inactive Only":
        include_inactive = True
        include_active = False
    else:
        include_inactive = False
        include_active = True

    entities = macros.Macros.query

    if include_inactive and not include_active:
        entities = entities.filter_by(active=False)
    elif not include_inactive and include_active:
        entities = entities.filter_by(active=True)

    entities = entities.all()

    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype='application/json')


@app.route('/ThreatKB/macros/<string:tag>', methods=['GET'])
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
        value=request.json['value'],
        active=request.json.get("active", True),
        created_user_id=current_user.id,
        modified_user_id=current_user.id
    )
    db.session.add(entity)
    db.session.commit()

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/macros/activate/<string:tag>', methods=['PUT'])
@auto.doc()
@login_required
def activate_macro(tag):
    entity = macros.Macros.query.get(tag)
    entity.active = 1

    db.session.merge(entity)
    db.session.commit()

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/macros/<string:tag>', methods=['PUT'])
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
        modified_user_id=current_user.id,
        active=request.json.get("active", entity.active)
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

    if entity.active:
        entity.active = False

        if not entity:
            abort(404)

        db.session.merge(entity)
        db.session.commit()
    else:
        db.session.delete(entity)
        db.session.commit()

    return jsonify(''), 204
