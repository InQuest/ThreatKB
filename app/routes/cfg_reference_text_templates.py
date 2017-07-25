from app import app, db
from app.models import cfg_reference_text_templates
from flask import abort, jsonify, request
import datetime
import json


@app.route('/InquestKB/cfg_reference_text_templates', methods=['GET'])
def get_all_cfg_reference_text_templates():
    entities = cfg_reference_text_templates.Cfg_reference_text_templates.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/cfg_reference_text_templates/<int:id>', methods=['GET'])
def get_cfg_reference_text_templates(id):
    entity = cfg_reference_text_templates.Cfg_reference_text_templates.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/InquestKB/cfg_reference_text_templates', methods=['POST'])
def create_cfg_reference_text_templates():
    entity = cfg_reference_text_templates.Cfg_reference_text_templates(
        template_text=request.json['template_text']
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/InquestKB/cfg_reference_text_templates/<int:id>', methods=['PUT'])
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


@app.route('/InquestKB/cfg_reference_text_templates/<int:id>', methods=['DELETE'])
def delete_cfg_reference_text_templates(id):
    entity = cfg_reference_text_templates.Cfg_reference_text_templates.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
