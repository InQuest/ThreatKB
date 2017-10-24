from app import app, db, auto
from app.models import tasks
from flask import abort, jsonify, request, Response
from flask.ext.login import login_required, current_user
from dateutil import parser
import json


@app.route('/ThreatKB/tasks', methods=['GET'])
@auto.doc()
@login_required
def get_all_tasks():
    """Return all active tasks
    Return: list of task dictionaries"""
    entities = tasks.Tasks.query.filter_by(active=True).all()

    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype='application/json')


@app.route('/ThreatKB/tasks/<int:id>', methods=['GET'])
@auto.doc()
def get_tasks(id):
    """Return task associated with given id
    Return: task dictionary"""
    entity = tasks.Tasks.query.get(id)
    if not entity:
        abort(404)

    return jsonify(entity.to_dict())


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

    return jsonify(''), 204
