from app import app, db
from app.models import c2ip
from flask import abort, jsonify, request
import datetime
import json


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
        date_created=datetime.datetime.strptime(request.json['date_created'], "%Y-%m-%d").date()
        , date_modified=datetime.datetime.strptime(request.json['date_modified'], "%Y-%m-%d").date()
        , ip=request.json['ip']
        , asn=request.json['asn']
        , country=request.json['country']
        , city=request.json['city']
        , state=request.json['state']
        , reference_link=request.json['reference_link']
        , reference_text=request.json['reference_text']
        , expiration_type=request.json['expiration_type']
        , expiration_timestamp=datetime.datetime.strptime(request.json['expiration_timestamp'], "%Y-%m-%d").date()
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/InquestKB/c2ips/<int:id>', methods=['PUT'])
def update_c2ip(id):
    entity = c2ip.C2ip.query.get(id)
    if not entity:
        abort(404)
    entity = c2ip.C2ip(
        date_created=datetime.datetime.strptime(request.json['date_created'], "%Y-%m-%d").date(),
        date_modified=datetime.datetime.strptime(request.json['date_modified'], "%Y-%m-%d").date(),
        ip=request.json['ip'],
        asn=request.json['asn'],
        country=request.json['country'],
        city=request.json['city'],
        state=request.json['state'],
        reference_link=request.json['reference_link'],
        reference_text=request.json['reference_text'],
        expiration_type=request.json['expiration_type'],
        expiration_timestamp=datetime.datetime.strptime(request.json['expiration_timestamp'], "%Y-%m-%d").date(),
        id=id
    )
    db.session.merge(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 200


@app.route('/InquestKB/c2ips/<int:id>', methods=['DELETE'])
def delete_c2ip(id):
    entity = c2ip.C2ip.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
