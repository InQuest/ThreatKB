from app import app, db, auto, ENTITY_MAPPING
from app.models import c2ip
from flask import abort, jsonify, request, Response, json
from flask_login import current_user, login_required
from dateutil import parser
from sqlalchemy import exc

from app.models.cfg_states import verify_state
from app.models.whitelist import WhitelistException
from app.routes.batch import batch_update, batch_delete
from app.routes.bookmarks import is_bookmarked, delete_bookmarks
from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping, get_tags_for_source, \
    batch_delete_tags_mapping_for_source_id
from app.routes.comments import create_comment
import distutils

from app.utilities import filter_entities


@app.route('/ThreatKB/c2ips', methods=['GET'])
@auto.doc()
@login_required
def get_all_c2ips():
    """Return a list of all c2ip artifacts.

    Optional URI Parameters:
    page_number: page number to start on, default 0
    page_size: the size of each page, default None (dont paginate)
    sort_by: column to sort by, must exist on the Yara_rule model, default None
    sort_direction: the direction to sort by if sorting, default ASC
    searches: dictionary of column filters as {column1:filter1, column2:filter2}, columns must exist on C2ip model or as dynamic metadata, default {}

    Return: list of c2ip artifact dictionaries"""

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
    operator = request.args.get('operator', 'and')
    sort_direction = request.args.get('sort_dir', 'ASC')
    exclude_totals = request.args.get('exclude_totals', False)
    include_metadata = bool(distutils.util.strtobool(request.args.get('include_metadata', "true")))
    include_tags = bool(distutils.util.strtobool(request.args.get('include_tags', "true")))
    include_comments = bool(distutils.util.strtobool(request.args.get('include_comments', "true")))

    response_dict = filter_entities(entity=c2ip.C2ip,
                                    artifact_type=ENTITY_MAPPING["IP"],
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
                                    default_sort="c2ip.date_created",
                                    operator=operator)

    return Response(response_dict, mimetype="application/json")


@app.route('/ThreatKB/c2ips/<id_or_ip>', methods=['GET'])
@auto.doc()
@login_required
def get_c2ip(id_or_ip):
    """Return c2ip artifact associated with the given id

    Optional URI Parameters:
    None

    Return: c2ip artifact dictionary"""
    if id_or_ip.isdigit():
        entity = c2ip.C2ip.query.get(int(id_or_ip))
    else:
        entity = c2ip.C2ip.query.filter(c2ip.C2ip.ip == id_or_ip).first()

    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)

    return_dict = entity.to_dict()
    return_dict["bookmarked"] = True if is_bookmarked(ENTITY_MAPPING["IP"], id, current_user.id) else False

    return jsonify(return_dict)


@app.route('/ThreatKB/c2ips', methods=['POST', 'PUT'])
@auto.doc()
@login_required
def create_c2ip():
    """Create c2ip artifact

    JSON Body: ip (str), asn (str), country (str), expiration_timestamp (date),  state(str)

    Return: c2dns artifact dictionary"""
    entity = c2ip.C2ip(
        ip=request.json['ip'],
        asn=request.json['asn'],
        country=request.json['country']['countryCode2'] if request.json.get("country", None) and request.json[
            "country"].get("countryCode2", None) else None,
        description=request.json.get("description", None),
        references=request.json.get("references", None),
        state=verify_state(request.json['state']['state'])
        if request.json['state'] and 'state' in request.json['state'] else verify_state(request.json['state']),
        expiration_timestamp=parser.parse(request.json['expiration_timestamp'])
        if request.json.get("expiration_timestamp", None) else None,
        created_user_id=current_user.id,
        modified_user_id=current_user.id,
        owner_user_id=current_user.id,
        active=request.json.get("active", True)
    )
    db.session.add(entity)
    try:
        db.session.commit()
    except exc.IntegrityError:
        app.logger.error("Duplicate IP: '%s'" % entity.ip)
        abort(409, description="Duplicate IP: '%s'" % entity.ip)
    except WhitelistException:
        app.logger.error("Whitelist validation failed.")
        abort(412, description="Whitelist validation failed.")

    entity.tags = create_tags_mapping(entity.__tablename__, entity.id, request.json['tags'])

    if request.json.get('new_comment', None):
        create_comment(request.json['new_comment'],
                       ENTITY_MAPPING["IP"],
                       entity.id,
                       current_user.id)

    entity.save_metadata(request.json.get("metadata_values", {}))

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/c2ip/activate/<id_or_ip>', methods=['PUT'])
@auto.doc()
@login_required
def activate_c2ip(id_or_ip):
    if id_or_ip.isdigit():
        entity = c2ip.C2ip.query.get(int(id_or_ip))
    else:
        entity = c2ip.C2ip.query.filter(c2ip.C2ip.ip == id_or_ip).first()

    entity.active = 1
    db.session.merge(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/c2ips/<id_or_ip>', methods=['PUT'])
@auto.doc()
@login_required
def update_c2ip(id_or_ip):
    """Update c2ip artifact
    From Data: ip (str), asn (str), country (str), expiration_timestamp (date), state(str)
    Return: c2dns artifact dictionary"""
    if id_or_ip.isdigit():
        entity = c2ip.C2ip.query.get(int(id_or_ip))
    else:
        entity = c2ip.C2ip.query.filter(c2ip.C2ip.ip == id_or_ip).first()

    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)
    entity = c2ip.C2ip(
        ip=request.json['ip'],
        asn=request.json['asn'],
        country=request.json['country']['countryCode2'] if request.json.get("country", None) and request.json[
            "country"].get("countryCode2", None) else None,
        description=request.json.get("description", None),
        references=request.json.get("references", None),
        state=verify_state(request.json['state']['state']) if request.json['state'] and 'state' in request.json['state']
        else verify_state(request.json['state']),
        expiration_timestamp=parser.parse(request.json['expiration_timestamp']) if request.json.get(
            "expiration_timestamp", None) else None,
        owner_user_id=request.json['owner_user']['id'] if request.json.get("owner_user", None) and request.json[
            "owner_user"].get("id", None) else None,
        id=entity.id,
        modified_user_id=current_user.id,
        active=request.json.get("active", entity.active)
    )
    db.session.merge(entity)

    try:
        db.session.commit()
    except exc.IntegrityError:
        app.logger.error("Duplicate IP: '%s'" % entity.ip)
        abort(409, description="Duplicate IP: '%s'" % entity.ip)
    except WhitelistException:
        app.logger.error("Whitelist validation failed.")
        abort(412, description="Whitelist validation failed.")

    current_tags = get_tags_for_source(entity.__tablename__, entity.id)
    new_tags = request.json['tags']
    tags_to_delete, tags_to_create = [c_tag for c_tag in current_tags if c_tag not in new_tags], [n_tag for n_tag in
                                                                                                  new_tags if
                                                                                                  n_tag not in current_tags]
    if tags_to_delete:
        batch_delete_tags_mapping_for_source_id(entity.__tablename__, entity.id, [tag['id'] for tag in tags_to_delete])
    if tags_to_create:
        create_tags_mapping(entity.__tablename__, entity.id, tags_to_create)

    entity.save_metadata(request.json.get("metadata_values", {}))

    entity = c2ip.C2ip.query.get(entity.id)
    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/c2ips/batch/edit', methods=['PUT'])
@auto.doc()
@login_required
def batch_update_c2ip():
    """Batch update c2ip artifacts
    From Data: batch {
                 state (str),
                 owner_user (str),
                 tags (array),
                 ids (array)
               }
    Return: Success Code"""

    if 'batch' in request.json and request.json['batch']:
        return batch_update(batch=request.json['batch'],
                            artifact=c2ip.C2ip,
                            session=db.session)


@app.route('/ThreatKB/c2ips/<id_or_ip>', methods=['DELETE'])
@auto.doc()
@login_required
def delete_c2ip(id_or_ip):
    """Delete c2ip artifact associated with id
    Return: None"""
    if id_or_ip.isdigit():
        entity = c2ip.C2ip.query.get(int(id_or_ip))
    else:
        entity = c2ip.C2ip.query.filter(c2ip.C2ip.ip == id_or_ip).first()

    if entity.active:
        entity.active = False

        if not entity:
            abort(404)

        if not current_user.admin and entity.owner_user_id != current_user.id:
            abort(403)

        db.session.merge(entity)
        db.session.commit()

        delete_tags_mapping(entity.__tablename__, entity.id)
        delete_bookmarks(ENTITY_MAPPING["IP"], id, current_user.id)
    else:
        db.session.delete(entity)
        db.session.commit()

        delete_tags_mapping(entity.__tablename__, entity.id)
        delete_bookmarks(ENTITY_MAPPING["IP"], id, current_user.id)

    return jsonify(''), 204


@app.route('/ThreatKB/c2ips/batch/delete', methods=['PUT'])
@auto.doc()
@login_required
def batch_delete_c2ip():
    """Batch delete c2ip artifacts
    From Data: batch {
                 ids (array)
               }
    Return: Success Code"""

    if 'batch' in request.json and request.json['batch']:
        return batch_delete(batch=request.json['batch'],
                            artifact=c2ip.C2ip,
                            session=db.session,
                            entity_mapping=ENTITY_MAPPING["IP"])


@app.route('/ThreatKB/c2ip/delete_all_inactive', methods=['PUT'])
@auto.doc()
@login_required
def delete_all_inactive_c2ip():
    db.session.query(c2ip.C2ip).filter(c2ip.C2ip.active == 0).delete()
    db.session.commit()
    return jsonify(''), 200
