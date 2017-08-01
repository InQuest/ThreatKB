from app import app, db
from app.models import c2ip
from flask import abort, jsonify, request
from flask.ext.login import current_user
from dateutil import parser
import datetime
import json

from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping



@app.route('/InquestKB/c2ips', methods=['GET'])
def get_all_c2ips():
    entities = c2ip.C2ip.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/c2ips/<int:id>', methods=['GET'])
def get_c2ip(id):
    entity = c2ip.C2ip.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/InquestKB/c2ips', methods=['POST'])
def create_c2ip():
    entity = c2ip.C2ip(
        ip=request.json['ip']
        , asn=request.json['asn']
        , country=request.json['country']
        , city=request.json['city']
        , st=request.json['st']
        , state=request.json['state']['state']
        , reference_link=request.json['reference_link']
        , reference_text=request.json['reference_text']
        , expiration_type=request.json['expiration_type']
        , expiration_timestamp=parser.parse(request.json['expiration_timestamp'])
        , created_user_id=current_user.id
        , modified_user_id=current_user.id
    )
    db.session.add(entity)
    db.session.commit()

    entity.tags = create_tags_mapping(entity.__tablename__, entity.id, request.json['tags'])

    return jsonify(entity.to_dict()), 201


@app.route('/InquestKB/c2ips/<int:id>', methods=['PUT'])
def update_c2ip(id):
    entity = c2ip.C2ip.query.get(id)
    if not entity:
        abort(404)
    entity = c2ip.C2ip(
        ip=request.json['ip'],
        asn=request.json['asn'],
        country=request.json['country'],
        city=request.json['city'],
        state=request.json['state']['state'],
        reference_link=request.json['reference_link'],
        reference_text=request.json['reference_text'],
        expiration_type=request.json['expiration_type'],
        expiration_timestamp=parser.parse(request.json['expiration_timestamp']),
        id=id,
        modified_user_id=current_user.id
    )
    db.session.merge(entity)
    db.session.commit()

    create_tags_mapping(entity.__tablename__, entity.id, request.json['addedTags'])
    delete_tags_mapping(entity.__tablename__, entity.id, request.json['removedTags'])

    return jsonify(entity.to_dict()), 200


@app.route('/InquestKB/c2ips/<int:id>', methods=['DELETE'])
def delete_c2ip(id):
    entity = c2ip.C2ip.query.get(id)
    tag_mapping_to_delete = entity.to_dict()['tags']

    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()

    delete_tags_mapping(entity.__tablename__, entity.id, tag_mapping_to_delete)

    return '', 204
