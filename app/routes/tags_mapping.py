from app import app, db
from app.models import tags_mapping
from flask import abort, jsonify, request
import datetime
import json


@app.route('/InquestKB/tags_mapping', methods=['GET'])
def get_all_tags_mapping():
    entities = tags_mapping.Tags_mapping.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/tags_mapping/<int:id>', methods=['GET'])
def get_tags_mapping(id):
    entity = tags_mapping.Tags_mapping.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/InquestKB/tags_mapping', methods=['POST'])
def create_tags_mapping():
    entity = tags_mapping.Tags_mapping(
        source_table=request.json['source_table'],
        source_id=request.json['source_id'],
        tag_id=request.json['tag_id']
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/InquestKB/tags_mapping/<int:id>', methods=['DELETE'])
def delete_tags_mapping(id):
    entity = tags_mapping.Tags_mapping.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
