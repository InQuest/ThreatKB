from app import app, db, auto, ENTITY_MAPPING
from app.models import c2ip
from flask import abort, jsonify, request, Response, json
from flask_login import current_user, login_required
from dateutil import parser
from sqlalchemy import exc

from app.models.cfg_states import verify_state
from app.routes.bookmarks import is_bookmarked, delete_bookmarks
from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping
from app.routes.comments import create_comment
import distutils

from app.utilities import filter_entities


@app.route('/ThreatKB/c2ips', methods=['GET'])
@auto.doc()
@login_required
def get_all_c2ips():
    """Return a list of all c2ip artifacts.

    Pagination variables:
    page_number: page number to start on, default 0
    page_size: the size of each page, default None (dont paginate)
    sort_by: column to sort by, must exist on the Yara_rule model, default None
    sort_direction: the direction to sort by if sorting, default ASC
    searches: dictionary of column filters as {column1:filter1, column2:filter2}, columns must exist on Yara_rule model, default {}

    Return: list of c2ip artifact dictionaries"""
    searches = request.args.get('searches', '{}')
    page_number = request.args.get('page_number', False)
    page_size = request.args.get('page_size', False)
    sort_by = request.args.get('sort_by', False)
    sort_direction = request.args.get('sort_dir', 'ASC')
    exclude_totals = request.args.get('exclude_totals', False)
    include_metadata = bool(distutils.util.strtobool(request.args.get('include_metadata', "true")))

    response_dict = filter_entities(entity=c2ip.C2ip,
                                    artifact_type=ENTITY_MAPPING["IP"],
                                    searches=searches,
                                    page_number=page_number,
                                    page_size=page_size,
                                    sort_by=sort_by,
                                    sort_direction=sort_direction,
                                    include_metadata=include_metadata,
                                    exclude_totals=exclude_totals,
                                    default_sort="c2ip.date_created")

    return Response(response_dict, mimetype="application/json")


@app.route('/ThreatKB/c2ips/<int:id>', methods=['GET'])
@auto.doc()
@login_required
def get_c2ip(id):
    """Return c2ip artifact associated with the given id
    Return: c2ip artifact dictionary"""
    entity = c2ip.C2ip.query.get(id)
    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)

    return_dict = entity.to_dict()
    return_dict["bookmarked"] = True if is_bookmarked(ENTITY_MAPPING["IP"], id, current_user.id) else False

    return jsonify(return_dict)


@app.route('/ThreatKB/c2ips', methods=['POST'])
@auto.doc()
@login_required
def create_c2ip():
    """Create c2ip artifact
    From Data: ip (str), asn (str), country (str),  expiration_type (str), expiration_timestamp (date),  state(str)
    Return: c2dns artifact dictionary"""
    entity = c2ip.C2ip(
        ip=request.json['ip'],
        asn=request.json['asn'],
        country=request.json['country'],
        description=request.json.get("description", None),
        references=request.json.get("references", None),
        state=verify_state(request.json['state']['state']),
        expiration_type=request.json['expiration_type'],
        expiration_timestamp=parser.parse(request.json['expiration_timestamp'])
        if request.json.get("expiration_type", None) else None,
        created_user_id=current_user.id,
        modified_user_id=current_user.id,
        owner_user_id=current_user.id
    )
    db.session.add(entity)
    try:
        db.session.commit()
    except exc.IntegrityError:
        app.logger.error("Duplicate IP: '%s'" % entity.ip)
        abort(409, description="Duplicate IP: '%s'" % entity.ip)
    except Exception:
        app.logger.error("Whitelist validation failed.")
        abort(412, description="Whitelist validation failed.")

    entity.tags = create_tags_mapping(entity.__tablename__, entity.id, request.json['tags'])

    if request.json['new_comment']:
        create_comment(request.json['new_comment'],
                       ENTITY_MAPPING["IP"],
                       entity.id,
                       current_user.id)

    entity.save_metadata(request.json.get("metadata_values", {}))

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/c2ips/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
def update_c2ip(id):
    """Update c2ip artifact
    From Data: ip (str), asn (str), country (str), expiration_type (str), expiration_timestamp (date), state(str)
    Return: c2dns artifact dictionary"""
    entity = c2ip.C2ip.query.get(id)
    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)
    entity = c2ip.C2ip(
        ip=request.json['ip'],
        asn=request.json['asn'],
        country=request.json['country'],
        description=request.json.get("description", None),
        references=request.json.get("references", None),
        state=verify_state(request.json['state']['state']) if request.json['state'] and 'state' in request.json['state']
        else verify_state(request.json['state']),
        expiration_type=request.json['expiration_type'],
        expiration_timestamp=parser.parse(request.json['expiration_timestamp']) if request.json.get(
            "expiration_timestamp", None) else None,
        owner_user_id=request.json['owner_user']['id'] if request.json.get("owner_user", None) and request.json[
            "owner_user"].get("id", None) else None,
        id=id,
        modified_user_id=current_user.id
    )
    db.session.merge(entity)

    try:
        db.session.commit()
    except exc.IntegrityError:
        app.logger.error("Duplicate IP: '%s'" % (entity.ip))
        abort(409, description="Duplicate IP: '%s'" % (entity.ip))

    create_tags_mapping(entity.__tablename__, entity.id, request.json['addedTags'])
    delete_tags_mapping(entity.__tablename__, entity.id, request.json['removedTags'])

    entity.save_metadata(request.json.get("metadata_values", {}))

    entity = c2ip.C2ip.query.get(entity.id)
    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/c2ips/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
def delete_c2ip(id):
    """Delete c2ip artifact associated with id
    Return: None"""
    entity = c2ip.C2ip.query.get(id)
    tag_mapping_to_delete = entity.to_dict()['tags']

    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)
    db.session.delete(entity)
    db.session.commit()

    delete_tags_mapping(entity.__tablename__, entity.id, tag_mapping_to_delete)
    delete_bookmarks(ENTITY_MAPPING["IP"], id, current_user.id)

    return jsonify(''), 204
