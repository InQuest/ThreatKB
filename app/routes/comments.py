from app import app, db
from app.models import comments
from flask import abort, jsonify, request
from flask.ext.login import login_required, current_user
import json

@app.route('/InquestKB/comments', methods=['GET'])
@login_required
def get_all_comments():
    app.logger.debug("args are: '%s'" % (request.args))
    entity_type = request.args.get("entity_type", None)
    entity_id = request.args.get("entity_id", None)
    entities = comments.Comments.query
    if entity_type:
        entities = entities.filter_by(entity_type=entity_type)
    if entity_id:
        entities = entities.filter_by(entity_id=entity_id)

    entities = entities.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/comments/<int:id>', methods=['GET'])
@login_required
def get_comments(id):
    entity = comments.Comments.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/InquestKB/comments', methods=['POST'])
@login_required
def create_comments():
    entity = comments.Comments(
        comment=request.json['comment']
        , entity_type=request.json['entity_type']
        , entity_id=request.json['entity_id']
        , user_id=current_user.id
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/InquestKB/comments/<int:id>', methods=['DELETE'])
@login_required
def delete_comments(id):
    entity = comments.Comments.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
