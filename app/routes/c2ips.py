from app import app, db, auto
from app.models import c2ip
from flask import abort, jsonify, request, Response
from flask.ext.login import current_user, login_required
from dateutil import parser
from sqlalchemy import exc
import json

from app.models.cfg_states import verify_state
from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping


@app.route('/ThreatKB/c2ips', methods=['GET'])
@auto.doc()
@login_required
def get_all_c2ips():
    """Return a list of all c2ip artifacts.
    Return: list of c2ip artifact dictionaries"""
    searches = request.args.get('searches', {})
    page_number = request.args.get('page_number', False)
    page_size = request.args.get('page_size', False)
    sort_by = request.args.get('sort_by', False)
    sort_direction = request.args.get('sort_dir', 'ASC')

    entities = c2ip.C2ip.query

    if not current_user.admin:
        entities = entities.filter_by(owner_user_id=current_user.id)

    for column, value in searches:
        try:
            column = getattr(c2ip.C2ip, column)
            entities = entities.filter(column.like("%" + str(value) + "%"))
        except:
            continue

    if sort_by:
        entities = entities.order_by("%s %s" % (sort_by, sort_direction))

    if page_size:
        entities = entities.limit(page_size)

    if page_number:
        entities = entities.offset(page_number * page_size)

    if not current_user.admin:
        entities = entities.filter_by(owner_user_id=current_user.id)

    entities = entities.all()

    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype='application/json')


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
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/c2ips', methods=['POST'])
@auto.doc()
@login_required
def create_c2ip():
    """Create c2ip artifact
    From Data: ip (str), asn (str), country (str), reference_link (str), expiration_type (str), expiration_timestamp (date), description (str), state(str)
    Return: c2dns artifact dictionary"""
    entity = c2ip.C2ip(
        ip=request.json['ip']
        , asn=request.json['asn']
        , country=request.json['country']
        , state=verify_state(request.json['state']['state'])
        , reference_link=request.json['reference_link']
        , expiration_type=request.json['expiration_type']
        , expiration_timestamp=parser.parse(request.json['expiration_timestamp']) if request.json.get("expiration_type",
                                                                                                      None) else None
        , description=request.json['description']
        , created_user_id=current_user.id
        , modified_user_id=current_user.id
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
    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/c2ips/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
def update_c2ip(id):
    """Update c2ip artifact
    From Data: ip (str), asn (str), country (str), reference_link (str), reference_text (str), expiration_type (str), expiration_timestamp (date), state(str), description (str)
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
        state=verify_state(request.json['state']['state']) if request.json['state'] and 'state' in request.json['state']
        else verify_state(request.json['state']),
        reference_link=request.json['reference_link'],
        expiration_type=request.json['expiration_type'],
        expiration_timestamp=parser.parse(request.json['expiration_timestamp']) if request.json.get(
            "expiration_timestamp", None) else None,
        owner_user_id=request.json['owner_user']['id'] if request.json.get("owner_user", None) and request.json[
            "owner_user"].get("id", None) else None,
        description = request.json['description'],
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

    return jsonify(''), 204
