from app import app, db
from app.models import c2dns
from flask import abort, jsonify, request
import datetime
import json

from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping


@app.route('/InquestKB/c2dns', methods=['GET'])
def get_all_c2dns():
    entities = c2dns.C2dns.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/c2dns/<int:id>', methods=['GET'])
def get_c2dns(id):
    entity = c2dns.C2dns.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/InquestKB/c2dns', methods=['POST'])
def create_c2dns():
    entity = c2dns.C2dns(
        date_created=datetime.datetime.strptime(request.json['date_created'], "%Y-%m-%d").date()
        , date_modified=datetime.datetime.strptime(request.json['date_modified'], "%Y-%m-%d").date()
        , state=request.json['state']
        , domain_name=request.json['domain_name']
        , match_type=request.json['match_type']
        , reference_link=request.json['reference_link']
        , reference_text=request.json['reference_text']
        , expiration_type=request.json['expiration_type']
        , expiration_timestamp=datetime.datetime.strptime(request.json['expiration_timestamp'], "%Y-%m-%d").date()
    )
    db.session.add(entity)
    db.session.commit()

    entity.tags = create_tags_mapping(entity.__tablename__, entity.id, request.json['tags'])

    return jsonify(entity.to_dict()), 201


@app.route('/InquestKB/c2dns/<int:id>', methods=['PUT'])
def update_c2dns(id):
    entity = c2dns.C2dns.query.get(id)
    if not entity:
        abort(404)
    entity = c2dns.C2dns(
        date_created=datetime.datetime.strptime(request.json['date_created'], "%Y-%m-%d").date(),
        date_modified=datetime.datetime.strptime(request.json['date_modified'], "%Y-%m-%d").date(),
        state=request.json['state'],
        domain_name=request.json['domain_name'],
        match_type=request.json['match_type'],
        reference_link=request.json['reference_link'],
        reference_text=request.json['reference_text'],
        expiration_type=request.json['expiration_type'],
        expiration_timestamp=datetime.datetime.strptime(request.json['expiration_timestamp'], "%Y-%m-%d").date(),
        id=id
    )
    db.session.merge(entity)
    db.session.commit()

    create_tags_mapping(entity.__tablename__, entity.id, request.json['addedTags'])
    delete_tags_mapping(entity.__tablename__, entity.id, request.json['removedTags'])

    return jsonify(entity.to_dict()), 200


@app.route('/InquestKB/c2dns/<int:id>', methods=['DELETE'])
def delete_c2dns(id):
    entity = c2dns.C2dns.query.get(id)
    tag_mapping_to_delete = entity.to_dict()['tags']

    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()

    delete_tags_mapping(entity.__tablename__, entity.id, tag_mapping_to_delete)

    return '', 204
