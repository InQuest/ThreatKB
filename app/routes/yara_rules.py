from app import app, db
from app.models import yara_rule
from flask import abort, jsonify, request
import datetime
import json


@app.route('/InquestKB/yara_rules', methods=['GET'])
def get_all_yara_rules():
    entities = yara_rule.Yara_rule.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/yara_rules/<int:id>', methods=['GET'])
def get_yara_rule(id):
    entity = yara_rule.Yara_rule.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/InquestKB/yara_rules', methods=['POST'])
def create_yara_rule():
    entity = yara_rule.Yara_rule(
        date_created=datetime.datetime.strptime(request.json['date_created'], "%Y-%m-%d").date()
        , date_modified=datetime.datetime.strptime(request.json['date_modified'], "%Y-%m-%d").date()
        , state=request.json['state']
        , name=request.json['name']
        , test_status=request.json['test_status']
        , confidence=request.json['confidence']
        , severity=request.json['severity']
        , description=request.json['description']
        , category=request.json['category']
        , file_type=request.json['file_type']
        , subcategory1=request.json['subcategory1']
        , subcategory2=request.json['subcategory2']
        , subcategory3=request.json['subcategory3']
        , reference_link=request.json['reference_link']
        , reference_text=request.json['reference_text']
        , condition=request.json['condition']
        , strings=request.json['strings']
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/InquestKB/yara_rules/<int:id>', methods=['PUT'])
def update_yara_rule(id):
    entity = yara_rule.Yara_rule.query.get(id)
    if not entity:
        abort(404)
    entity = yara_rule.Yara_rule(
        date_created=datetime.datetime.strptime(request.json['date_created'], "%Y-%m-%d").date(),
        date_modified=datetime.datetime.strptime(request.json['date_modified'], "%Y-%m-%d").date(),
        state=request.json['state'],
        name=request.json['name'],
        test_status=request.json['test_status'],
        confidence=request.json['confidence'],
        severity=request.json['severity'],
        description=request.json['description'],
        category=request.json['category'],
        file_type=request.json['file_type'],
        subcategory1=request.json['subcategory1'],
        subcategory2=request.json['subcategory2'],
        subcategory3=request.json['subcategory3'],
        reference_link=request.json['reference_link'],
        reference_text=request.json['reference_text'],
        condition=request.json['condition'],
        strings=request.json['strings'],
        id=id
    )
    db.session.merge(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 200


@app.route('/InquestKB/yara_rules/<int:id>', methods=['DELETE'])
def delete_yara_rule(id):
    entity = yara_rule.Yara_rule.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
