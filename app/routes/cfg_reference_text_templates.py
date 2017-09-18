from app import app, db, admin_only, auto
from app.models import cfg_reference_text_templates
from flask import abort, jsonify, request
from flask.ext.login import login_required
import json


@app.route('/ThreatKB/cfg_reference_text_templates', methods=['GET'])
@auto.doc()
@login_required
def get_all_cfg_reference_text_templates():
    """Return list of all reference text templates
    Return: list of reference text templates dictionaries"""
    entities = cfg_reference_text_templates.Cfg_reference_text_templates.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/ThreatKB/cfg_reference_text_templates/<int:id>', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_cfg_reference_text_templates(id):
    """Return reference text template associated with the given id
    Return: reference text template dictionary"""
    entity = cfg_reference_text_templates.Cfg_reference_text_templates.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/cfg_reference_text_templates', methods=['POST'])
@auto.doc()
@login_required
@admin_only()
def create_cfg_reference_text_templates():
    """Create reference text template
    Retun: reference text template dictionary"""
    entity = cfg_reference_text_templates.Cfg_reference_text_templates(
        template_text=request.json['template_text']
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/cfg_reference_text_templates/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
def update_cfg_reference_text_templates(id):
    """Update reference text template associated with the given id
    From Data: template_text (str)
    Return: reference text template dictionary"""
    entity = cfg_reference_text_templates.Cfg_reference_text_templates.query.get(id)
    if not entity:
        abort(404)
    entity = cfg_reference_text_templates.Cfg_reference_text_templates(
        template_text=request.json['template_text'],
        id=id
    )
    db.session.merge(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/cfg_reference_text_templates/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_cfg_reference_text_templates(id):
    """Delete reference text template associated with the given id
    Return: None"""
    entity = cfg_reference_text_templates.Cfg_reference_text_templates.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
