from app import app, db, auto, ENTITY_MAPPING
from app.models import tasks
from flask import abort, jsonify, request, Response
from flask.ext.login import login_required, current_user
from dateutil import parser
import json
from sqlalchemy import or_

from app.models.bookmarks import Bookmarks
from app.routes.bookmarks import is_bookmarked, delete_bookmarks


@app.route('/ThreatKB/tasks', methods=['GET'])
@auto.doc()
@login_required
def get_all_tasks():
    """Return all active tasks
    Return: list of task dictionaries"""
    entities = tasks.Tasks.query.filter_by(active=True)


    if current_user.admin:
        entities = entities.order_by("date_created DESC").all()
    else:
        entities = entities.filter(
            or_(tasks.Tasks.owner_user_id == current_user.id, tasks.Tasks.owner_user_id == None)).order_by(
            "date_created DESC").all()

    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype='application/json')


@app.route('/ThreatKB/tasks/<int:id>', methods=['GET'])
@login_required
@auto.doc()
def get_tasks(id):
    """Return task associated with given id
    Return: task dictionary"""
    entity = tasks.Tasks.query.get(id)
    if not entity:
        abort(404)

    if not current_user.admin and not entity.owner_user_id == current_user.id and not entity.owner_user_id == None:
        return jsonify({})

    return_dict = entity.to_dict()
    return_dict["bookmarked"] = True if is_bookmarked(ENTITY_MAPPING["TASK"], id, current_user.id) else False

    return jsonify(return_dict)


@app.route('/ThreatKB/tasks', methods=['POST'])
@auto.doc()
@login_required
def create_tasks():
    """Create new task
    From Data: title (str), description (str), final_artifact(str), state (str)
    Return: task dictionary"""
    entity = tasks.Tasks(
        title=request.json['title']
        , description=request.json['description']
        , final_artifact=request.json['final_artifact']
        , state=request.json['state']['state'] if 'state' in request.json['state'] else None
        , created_user_id=current_user.id
        , modified_user_id=current_user.id
    )
    db.session.add(entity)
    db.session.commit()

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/tasks/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
def update_tasks(id):
    """Update task associated with given id
    From Data: title (str), description (str), final_artifact(str), state (str)
    Return: task dictionary"""
    entity = tasks.Tasks.query.get(id)
    if not entity:
        abort(404)

    entity.title = request.json['title']
    entity.description = request.json['description']
    entity.final_artifact = request.json['final_artifact']
    entity.state = request.json['state']['state'] if request.json['state'] and 'state' in request.json['state'] else \
        request.json['state']
    entity.created_user_id = current_user.id
    entity.modified_user_id = current_user.id
    entity.owner_user_id = request.json['owner_user']['id'] if request.json.get("owner_user", None) and request.json[
        "owner_user"].get("id", None) else None,

    db.session.commit()

    entity = tasks.Tasks.query.filter(tasks.Tasks.id == entity.id).first()
    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/tasks/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
def delete_tasks(id):
    """Delete task associated with the given id
    Return: None"""
    entity = tasks.Tasks.query.get(id)

    if not entity:
        abort(404)

    # db.session.delete(entity)
    entity.active = False
    db.session.add(entity)
    db.session.commit()

    delete_bookmarks(ENTITY_MAPPING["TASK"], id, current_user.id)

    return jsonify(''), 204
