from app import app, db
from app.models import cfg_reference_text_templates
from flask import abort, jsonify, request
from flask.ext.login import login_required
import json


@app.route('/ThreatKB/cfg_reference_text_templates', methods=['GET'])
@login_required
def get_all_cfg_reference_text_templates():
    entities = cfg_reference_text_templates.Cfg_reference_text_templates.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/ThreatKB/cfg_reference_text_templates/<int:id>', methods=['GET'])
@login_required
def get_cfg_reference_text_templates(id):
    entity = cfg_reference_text_templates.Cfg_reference_text_templates.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/cfg_reference_text_templates', methods=['POST'])
@login_required
def create_cfg_reference_text_templates():
    entity = cfg_reference_text_templates.Cfg_reference_text_templates(
        template_text=request.json['template_text']
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/cfg_reference_text_templates/<int:id>', methods=['PUT'])
@login_required
def update_cfg_reference_text_templates(id):
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
@login_required
def delete_cfg_reference_text_templates(id):
    entity = cfg_reference_text_templates.Cfg_reference_text_templates.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
