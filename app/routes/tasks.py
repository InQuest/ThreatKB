from app import app, db
from app.models import tasks
from flask import abort, jsonify, request
from flask.ext.login import login_required, current_user
from dateutil import parser
import json


@app.route('/ThreatKB/tasks', methods=['GET'])
@login_required
def get_all_tasks():
    entities = tasks.Tasks.query.all()

    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/ThreatKB/tasks/<int:id>', methods=['GET'])
def get_tasks(id):
    entity = tasks.Tasks.query.get(id)
    if not entity:
        abort(404)

    return jsonify(entity.to_dict())


@app.route('/ThreatKB/tasks', methods=['POST'])
@login_required
def create_tasks():
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
@login_required
def update_tasks(id):
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
@login_required
def delete_tasks(id):
    entity = tasks.Tasks.query.get(id)

    if not entity:
        abort(404)

    db.session.delete(entity)
    db.session.commit()

    return '', 204
