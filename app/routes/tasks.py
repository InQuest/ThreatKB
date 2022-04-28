from distutils import util

from app import app, db, auto, ENTITY_MAPPING
from app.models import tasks, cfg_settings
from flask import abort, jsonify, request, Response
from flask_login import login_required, current_user
from app.routes.batch import batch_update
from app.routes.bookmarks import is_bookmarked, delete_bookmarks

from app.utilities import filter_entities


@app.route('/ThreatKB/tasks', methods=['GET'])
@auto.doc()
@login_required
def get_all_tasks():
    """Return all active tasks

    Pagination variables:
    page_number: page number to start on, default 0
    page_size: the size of each page, default None (don't paginate)
    sort_by: column to sort by, must exist on the Task model, default None
    sort_direction: the direction to sort by if sorting, default ASC
    searches: dictionary of column filters as {column1:filter1, column2:filter2}, columns must exist on Task model, default {}

    Return: list of task dictionaries"""
    searches = request.args.get('searches', '{}')
    page_number = request.args.get('page_number', False)
    page_size = request.args.get('page_size', False)
    sort_by = request.args.get('sort_by', False)
    sort_direction = request.args.get('sort_dir', 'ASC')
    exclude_totals = request.args.get('exclude_totals', False)
    include_metadata = bool(util.strtobool(request.args.get('include_metadata', "false")))
    include_tags = bool(util.strtobool(request.args.get('include_tags', "true")))
    include_comments = bool(util.strtobool(request.args.get('include_comments', "true")))

    response_dict = filter_entities(entity=tasks.Tasks,
                                    artifact_type=ENTITY_MAPPING["TASK"],
                                    searches=searches,
                                    page_number=page_number,
                                    page_size=page_size,
                                    sort_by=sort_by,
                                    sort_direction=sort_direction,
                                    include_metadata=include_metadata,
                                    include_tags=include_tags,
                                    include_comments=include_comments,
                                    exclude_totals=exclude_totals,
                                    default_sort="date_created",
                                    include_inactive=False)

    return Response(response_dict, mimetype='application/json')


@app.route('/ThreatKB/tasks/<int:id>', methods=['GET'])
@login_required
@auto.doc()
def get_tasks(id):
    """Return task associated with given id
    Return: task dictionary"""
    entity = tasks.Tasks.query.get(id)
    if not entity:
        abort(404, description="You have requested a resource that is not in the database")

    show_for_non_admin = cfg_settings.Cfg_settings.get_setting("ENABLE_NON_ADMIN_TASK_VISIBILITY")
    show_for_non_admin = bool(util.strtobool(show_for_non_admin)) if show_for_non_admin else False

    if not show_for_non_admin and \
            not (current_user.admin or entity.owner_user_id == current_user.id or entity.owner_user_id is None):
        return jsonify({})

    return_dict = entity.to_dict()
    return_dict["bookmarked"] = True if is_bookmarked(ENTITY_MAPPING["TASK"], id, current_user.id) else False

    return jsonify(return_dict)


@app.route('/ThreatKB/tasks', methods=['POST', 'PUT'])
@auto.doc()
@login_required
def create_tasks():
    """Create new task
    From Data: title (str), description (str), final_artifact(str), state (str)
    Return: task dictionary"""
    entity = tasks.Tasks(
        title=request.json['title'],
        description=request.json['description'],
        final_artifact=request.json['final_artifact'] if "final_artifact" in request.json else None,
        state=request.json['state']['state'] if 'state' in request.json['state'] else None,
        created_user_id=current_user.id,
        modified_user_id=current_user.id,
        owner_user_id=current_user.id
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
    final_artifact = request.json['final_artifact'] if "final_artifact" in request.json else None,
    entity.state = request.json['state']['state'] if request.json['state'] and 'state' in request.json['state'] else \
        request.json['state']
    entity.created_user_id = current_user.id
    entity.modified_user_id = current_user.id
    entity.owner_user_id = request.json['owner_user']['id'] if request.json.get("owner_user", None) and request.json[
        "owner_user"].get("id", None) else None,

    db.session.commit()

    entity = tasks.Tasks.query.filter(tasks.Tasks.id == entity.id).first()
    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/tasks/batch/edit', methods=['PUT'])
@auto.doc()
@login_required
def batch_update_tasks():
    """Batch update task artifacts
    From Data: batch {
                 state (str),
                 owner_user (str),
                 ids (array)
               }
    Return: Success"""

    if 'batch' in request.json and request.json['batch']:
        return batch_update(batch=request.json['batch'],
                            artifact=tasks.Tasks,
                            session=db.session,
                            entity_mapping=ENTITY_MAPPING["TASK"],
                            include_tags=False)


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
