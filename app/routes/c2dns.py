from app import app, db, auto, ENTITY_MAPPING
from app.models import c2dns
from flask import abort, jsonify, request, Response, json
from flask_login import login_required, current_user
from dateutil import parser
from sqlalchemy import exc

from app.models.cfg_states import verify_state
from app.routes.batch import batch_update, batch_delete
from app.routes.bookmarks import is_bookmarked, delete_bookmarks
from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping
from app.routes.comments import create_comment
import distutils

from app.utilities import filter_entities


@app.route('/ThreatKB/c2dns', methods=['GET'])
@auto.doc()
@login_required
def get_all_c2dns():
    """Return a list of all c2dns artifacts.

    Pagination variables:
    page_number: page number to start on, default 0
    page_size: the size of each page, default None (dont paginate)
    sort_by: column to sort by, must exist on the Yara_rule model, default None
    sort_direction: the direction to sort by if sorting, default ASC
    searches: dictionary of column filters as {column1:filter1, column2:filter2}, columns must exist on Yara_rule model, default {}

    Return: list of c2dns artifact dictionaries
    """

    view = request.args.get("view", "Active Only")

    if view == "All":
        include_inactive = True
        include_active = True
    elif view == "Active Only":
        include_inactive = False
        include_active = True
    elif view == "Inactive Only":
        include_inactive = True
        include_active = False
    else:
        include_inactive = False
        include_active = True

    searches = request.args.get('searches', '{}')
    page_number = request.args.get('page_number', False)
    page_size = request.args.get('page_size', False)
    sort_by = request.args.get('sort_by', False)
    sort_direction = request.args.get('sort_dir', 'ASC')
    operator = request.args.get('operator', 'and')
    exclude_totals = request.args.get('exclude_totals', False)
    include_metadata = bool(distutils.util.strtobool(request.args.get('include_metadata', "true")))
    include_tags = bool(distutils.util.strtobool(request.args.get('include_tags', "true")))
    include_comments = bool(distutils.util.strtobool(request.args.get('include_comments', "true")))

    response_dict = filter_entities(entity=c2dns.C2dns,
                                    artifact_type=ENTITY_MAPPING["DNS"],
                                    searches=searches,
                                    page_number=page_number,
                                    page_size=page_size,
                                    sort_by=sort_by,
                                    sort_direction=sort_direction,
                                    include_metadata=include_metadata,
                                    include_inactive=include_inactive,
                                    include_tags=include_tags,
                                    include_comments=include_comments,
                                    include_active=include_active,
                                    exclude_totals=exclude_totals,
                                    default_sort="c2dns.date_created",
                                    operator=operator)

    return Response(response_dict, mimetype="application/json")


@app.route('/ThreatKB/c2dns/<int:id>', methods=['GET'])
@auto.doc()
def get_c2dns(id):
    """Return c2dns artifact associated with the given id
    Return: c2dns artifact dictionary"""
    entity = c2dns.C2dns.query.get(id)
    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)

    return_dict = entity.to_dict()
    return_dict["bookmarked"] = True if is_bookmarked(ENTITY_MAPPING["DNS"], id, current_user.id) else False

    return jsonify(return_dict)


@app.route('/ThreatKB/c2dns', methods=['POST'])
@auto.doc()
@login_required
def create_c2dns():
    """Create c2dns artifact
    From Data: domain_name (str), match_type (str), expiration_timestamp (date), state(str)
    Return: c2dns artifact dictionary"""
    entity = c2dns.C2dns(
        domain_name=request.json['domain_name'],
        match_type=request.json['match_type'],
        description=request.json.get("description", None),
        references=request.json.get("references", None),
        expiration_timestamp=parser.parse(request.json['expiration_timestamp'])
        if request.json.get("expiration_timestamp", None) else None,
        state=verify_state(request.json['state']['state'])
        if request.json['state'] and 'state' in request.json['state'] else verify_state(request.json['state']),
        created_user_id=current_user.id,
        modified_user_id=current_user.id,
        owner_user_id=current_user.id,
        active=request.json.get("active", True)
    )
    db.session.add(entity)

    try:
        db.session.commit()
    except exc.IntegrityError:
        app.logger.error("Duplicate DNS: '%s'" % entity.domain_name)
        abort(409)
    except Exception as e:
        app.logger.error("Whitelist validation failed.")
        abort(412, description="Whitelist validation failed.")

    entity.tags = create_tags_mapping(entity.__tablename__, entity.id, request.json['tags'])

    if request.json.get('new_comment', None):
        create_comment(request.json['new_comment'],
                       ENTITY_MAPPING["DNS"],
                       entity.id,
                       current_user.id)

    entity.save_metadata(request.json.get("metadata_values", {}))

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/c2dns/activate/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
def activate_c2dns(id):
    entity = c2dns.C2dns.query.get(id)
    entity.active = 1
    db.session.merge(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/c2dns/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
def update_c2dns(id):
    """Update c2dns artifact
    From Data: domain_name (str), match_type (str), expiration_timestamp (date), state(str)
    Return: c2dns artifact dictionary"""
    entity = c2dns.C2dns.query.get(id)
    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)
    entity = c2dns.C2dns(
        state=verify_state(request.json['state']['state']) if request.json['state'] and 'state' in request.json['state']
        else verify_state(request.json['state']),
        domain_name=request.json['domain_name'],
        match_type=request.json['match_type'],
        description=request.json.get("description", None),
        references=request.json.get("references", None),
        expiration_timestamp=parser.parse(request.json['expiration_timestamp']) if request.json.get(
            "expiration_timestamp", None) else None,
        id=id,
        owner_user_id=request.json['owner_user']['id'] if request.json.get("owner_user", None) and request.json[
            "owner_user"].get("id", None) else None,
        modified_user_id=current_user.id,
        active=request.json.get("active", entity.active)
    )
    db.session.merge(entity)

    try:
        db.session.commit()
    except exc.IntegrityError:
        app.logger.error("Duplicate DNS: '%s'" % entity.domain_name)
        abort(409, description="Duplicate DNS: '%s'" % entity.domain_name)

    delete_tags_mapping(entity.__tablename__, entity.id)
    create_tags_mapping(entity.__tablename__, entity.id, request.json['tags'])

    entity.save_metadata(request.json.get("metadata_values", {}))

    entity = c2dns.C2dns.query.get(entity.id)
    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/c2dns/batch/edit', methods=['PUT'])
@auto.doc()
@login_required
def batch_update_c2dns():
    """Batch update c2dns artifacts
    From Data: batch {
                 state (str),
                 owner_user (str),
                 tags (array),
                 ids (array)
               }
    Return: Success Code"""

    if 'batch' in request.json and request.json['batch']:
        return batch_update(batch=request.json['batch'],
                            artifact=c2dns.C2dns,
                            session=db.session)


@app.route('/ThreatKB/c2dns/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
def delete_c2dns(id):
    """Delete c2dns artifact associated with id
    Return: None"""
    entity = c2dns.C2dns.query.get(id)

    if entity.active:
        entity.active = False

        if not entity:
            abort(404)

        if not current_user.admin and entity.owner_user_id != current_user.id:
            abort(403)

        db.session.merge(entity)
        db.session.commit()
        delete_tags_mapping(entity.__tablename__, entity.id)
        delete_bookmarks(ENTITY_MAPPING["DNS"], id, current_user.id)
    else:
        db.session.delete(entity)
        db.session.commit()
        delete_tags_mapping(entity.__tablename__, entity.id)
        delete_bookmarks(ENTITY_MAPPING["DNS"], id, current_user.id)

    return jsonify(''), 204


@app.route('/ThreatKB/c2dns/batch/delete', methods=['PUT'])
@auto.doc()
@login_required
def batch_delete_c2dns():
    """Batch delete c2dns artifacts
    From Data: batch {
                 ids (array)
               }
    Return: Success Code"""

    if 'batch' in request.json and request.json['batch']:
        return batch_delete(batch=request.json['batch'],
                            artifact=c2dns.C2dns,
                            session=db.session,
                            entity_mapping=ENTITY_MAPPING["DNS"])


@app.route('/ThreatKB/c2dns/delete_all_inactive', methods=['PUT'])
@auto.doc()
@login_required
def delete_all_inactive_c2dns():
    db.session.query(c2dns.C2dns).filter(c2dns.C2dns.active == 0).delete()
    db.session.commit()
    return jsonify(''), 200
