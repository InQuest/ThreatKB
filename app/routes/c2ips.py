from app import app, db, auto, ENTITY_MAPPING
from app.models import c2ip
from flask import abort, jsonify, request, Response, json
from flask.ext.login import current_user, login_required
from dateutil import parser
from sqlalchemy import exc, and_

from app.models.users import KBUser
from app.models.bookmarks import Bookmarks
from app.models.metadata import Metadata, MetadataMapping, MetadataChoices
from app.models.cfg_states import verify_state
from app.routes.bookmarks import is_bookmarked, delete_bookmarks
from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping


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

    searches = json.loads(searches)

    if searches and not any([search_key in c2ip.C2ip.__table__.columns.keys() for search_key, val in searches.items()]):
        entities = c2ip.C2ip.query.outerjoin(Metadata, Metadata.artifact_type == ENTITY_MAPPING["IP"]).join(
            MetadataMapping,
            and_(
                MetadataMapping.metadata_id == Metadata.id,
                MetadataMapping.artifact_id == c2ip.C2ip.id))
    else:
        entities = c2ip.C2ip.query

    if not current_user.admin:
        entities = entities.filter_by(owner_user_id=current_user.id)

    for column, value in searches.items():
        if not value:
            continue

        if column == "owner_user.email":
            entities = entities.join(KBUser, c2ip.C2ip.owner_user_id == KBUser.id).filter(
                KBUser.email.like("%" + str(value) + "%"))
            continue

        try:
            column = getattr(c2ip.C2ip, column)
            entities = entities.filter(column.like("%" + str(value) + "%"))
        except AttributeError, e:
            entities = entities.filter(and_(MetadataMapping.artifact_id == c2ip.C2ip.id, Metadata.key == column,
                                            MetadataMapping.value.like("%" + str(value) + "%")))

    filtered_entities = entities
    total_count = entities.count()

    if sort_by:
        filtered_entities = filtered_entities.order_by("%s %s" % (sort_by, sort_direction))
    else:
        filtered_entities = filtered_entities.order_by("c2ip.date_created DESC")

    if page_size:
        filtered_entities = filtered_entities.limit(int(page_size))

    if page_number:
        filtered_entities = filtered_entities.offset(int(page_number) * int(page_size))

    filtered_entities = filtered_entities.all()

    response_dict = dict()
    response_dict['data'] = [entity.to_dict() for entity in filtered_entities]
    response_dict['total_count'] = total_count

    return Response(json.dumps(response_dict), mimetype='application/json')


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
        ip=request.json['ip']
        , asn=request.json['asn']
        , country=request.json['country']
        , description=request.json.get("description", None)
        , references=request.json.get("references", None)
        , state=verify_state(request.json['state']['state'])
        , expiration_type=request.json['expiration_type']
        , expiration_timestamp=parser.parse(request.json['expiration_timestamp']) if request.json.get("expiration_type",
                                                                                                      None) else None
        , created_user_id=current_user.id
        , modified_user_id=current_user.id
        , owner_user_id=current_user.id
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
