from app import app, db
from app.models import tags
from flask import abort, jsonify, request
import datetime
import json

@app.route('/InquestKB/tags', methods = ['GET'])
def get_all_tags():
    entities = tags.Tags.query.all()
    return json.dumps([entity.to_dict() for entity in entities])

@app.route('/InquestKB/tags/<int:id>', methods = ['GET'])
def get_tags(id):
    entity = tags.Tags.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())

@app.route('/InquestKB/tags', methods = ['POST'])
def create_tags():
    entity = tags.Tags(
        text = request.json['text']
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201

@app.route('/InquestKB/tags/<int:id>', methods = ['PUT'])
def update_tags(id):
    entity = tags.Tags.query.get(id)
    if not entity:
        abort(404)
    entity = tags.Tags(
        text = request.json['text'],
        id = id
    )
    db.session.merge(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 200

@app.route('/InquestKB/tags/<int:id>', methods = ['DELETE'])
def delete_tags(id):
    entity = tags.Tags.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
