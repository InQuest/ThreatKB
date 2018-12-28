from app import app, db, admin_only, auto
from app.models import comments
from flask import abort, jsonify, request, Response
from flask_login import login_required, current_user
import json


@app.route('/ThreatKB/comments', methods=['GET'])
@auto.doc()
@login_required
def get_all_comments():
    """Return all comments
    Optional Arguments: entity_type (int) {"SIGNATURE": 1, "DNS": 2, "IP": 3, "TASK": 4}, entity_id (int)
    Return: list of comment dictionaries"""
    app.logger.debug("args are: '%s'" % (request.args))
    entity_type = request.args.get("entity_type", None)
    entity_id = request.args.get("entity_id", None)
    entities = comments.Comments.query
    if entity_type:
        entities = entities.filter_by(entity_type=entity_type)
    if entity_id:
        entities = entities.filter_by(entity_id=entity_id)

    entities = entities.all()
    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype='application/json')


@app.route('/ThreatKB/comments/<int:id>', methods=['GET'])
@auto.doc()
@login_required
def get_comments(id):
    """Return comment associated with the given id
    Return: comment dictionary"""
    entity = comments.Comments.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/comments', methods=['POST'])
@auto.doc()
@login_required
def create_comments():
    """Create comment
    From Data: comment (str), entity_type (int) {"SIGNATURE": 1, "DNS": 2, "IP": 3, "TASK": 4}, entity_id
    Return: comment dictionary"""

    return create_comment(request.json['comment'],
                          request.json['entity_type'],
                          request.json['entity_id'],
                          current_user.id), 201


def create_comment(comment, entity_type, entity_id, user_id):
    entity = comments.Comments(
        comment=comment,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/comments/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_comments(id):
    """Delete comment associated with the given id
    Return: None"""
    entity = comments.Comments.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return jsonify(''), 204
