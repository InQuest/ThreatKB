from app import app, db
from app.models import tags
from flask import abort, jsonify, request
from flask.ext.login import login_required
import json


@app.route('/InquestKB/tags', methods=['GET'])
@login_required
def get_all_tags():
    entities = tags.Tags.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/tags/<int:id>', methods=['GET'])
@login_required
def get_tags(id):
    entity = tags.Tags.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/InquestKB/tags', methods=['POST'])
@login_required
def create_tags():
    created_tag = create_tag(request.json['text'])
    return jsonify(created_tag.to_dict()), 201


def create_tag(tag_text):
    entity = tags.Tags(
        text=tag_text
    )
    db.session.add(entity)
    db.session.commit()
    return entity


@app.route('/InquestKB/tags/<int:id>', methods=['PUT'])
@login_required
def update_tags(id):
    entity = tags.Tags.query.get(id)
    if not entity:
        abort(404)
    entity = tags.Tags(
        text=request.json['text'],
        id=id
    )
    db.session.merge(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 200


@app.route('/InquestKB/tags/<int:id>', methods=['DELETE'])
@login_required
def delete_tags(id):
    entity = tags.Tags.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
