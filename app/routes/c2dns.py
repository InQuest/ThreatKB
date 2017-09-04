from app import app, db
from app.models import c2dns
from flask import abort, jsonify, request
from flask.ext.login import login_required, current_user
from dateutil import parser
import json

from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping


@app.route('/InquestKB/c2dns', methods=['GET'])
@login_required
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
@login_required
def create_c2dns():
    entity = c2dns.C2dns(
        domain_name=request.json['domain_name']
        , match_type=request.json['match_type']
        , reference_link=request.json['reference_link']
        , reference_text=request.json['reference_text']
        , expiration_type=request.json['expiration_type']
        , expiration_timestamp=parser.parse(request.json['expiration_timestamp']) if request.json.get("expiration_type",
                                                                                                      None) else None
        , state=request.json['state']['state']
        , created_user_id=current_user.id
        , modified_user_id=current_user.id
    )
    db.session.add(entity)
    db.session.commit()

    entity.tags = create_tags_mapping(entity.__tablename__, entity.id, request.json['tags'])

    return jsonify(entity.to_dict()), 201


@app.route('/InquestKB/c2dns/<int:id>', methods=['PUT'])
@login_required
def update_c2dns(id):
    entity = c2dns.C2dns.query.get(id)
    if not entity:
        abort(404)
    entity = c2dns.C2dns(
        state=request.json['state']['state'],
        domain_name=request.json['domain_name'],
        match_type=request.json['match_type'],
        reference_link=request.json['reference_link'],
        reference_text=request.json['reference_text'],
        expiration_type=request.json['expiration_type'],
        expiration_timestamp=parser.parse(request.json['expiration_timestamp']) if request.json.get(
            "expiration_timestamp", None) else None,
        id=id,
        modified_user_id=current_user.id
    )
    db.session.merge(entity)
    db.session.commit()

    create_tags_mapping(entity.__tablename__, entity.id, request.json['addedTags'])
    delete_tags_mapping(entity.__tablename__, entity.id, request.json['removedTags'])

    entity = c2dns.C2dns.query.get(entity.id)
    return jsonify(entity.to_dict()), 200


@app.route('/InquestKB/c2dns/<int:id>', methods=['DELETE'])
@login_required
def delete_c2dns(id):
    entity = c2dns.C2dns.query.get(id)
    tag_mapping_to_delete = entity.to_dict()['tags']

    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()

    delete_tags_mapping(entity.__tablename__, entity.id, tag_mapping_to_delete)

    return '', 204
