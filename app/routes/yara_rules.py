from app import app, db
from app.models import yara_rule
from flask import abort, jsonify, request
from flask.ext.login import current_user, login_required

from app.routes.cfg_category_range_mapping import update_cfg_category_range_mapping_current
from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping
import json
import datetime


@app.route('/ThreatKB/yara_rules', methods=['GET'])
@login_required
def get_all_yara_rules():
    include_inactive = request.args.get("include_inactive", False)

    if include_inactive:
        entities = yara_rule.Yara_rule.all()
    else:
        entities = yara_rule.Yara_rule.query.filter_by(active=True).all()

    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/ThreatKB/yara_rules/<int:id>', methods=['GET'])
@login_required
def get_yara_rule(id):
    entity = yara_rule.Yara_rule.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/yara_rules', methods=['POST'])
@login_required
def create_yara_rule():
    new_sig_id = 0
    if request.json['category'] and 'category' in request.json['category']:
        new_sig_id = request.json['category']['current'] + 1

    entity = yara_rule.Yara_rule(
        state=request.json['state']['state'] if 'state' in request.json['state'] else None
        , name=request.json['name']
        , test_status=request.json['test_status']
        , confidence=request.json['confidence']
        , severity=request.json['severity']
        , description=request.json['description']
        , category=request.json['category']['category'] if 'category' in request.json['category'] else None
        , file_type=request.json['file_type']
        , subcategory1=request.json['subcategory1']
        , subcategory2=request.json['subcategory2']
        , subcategory3=request.json['subcategory3']
        , reference_link=request.json['reference_link']
        , reference_text=request.json['reference_text']
        , condition=yara_rule.Yara_rule.make_yara_sane(request.json['condition'], "condition:")
        , strings=yara_rule.Yara_rule.make_yara_sane(request.json['strings'], "strings:")
        , signature_id=new_sig_id
        , created_user_id=current_user.id
        , modified_user_id=current_user.id
    )
    db.session.add(entity)
    db.session.commit()

    entity.tags = create_tags_mapping(entity.__tablename__, entity.id, request.json['tags'])
    if new_sig_id > 0:
        update_cfg_category_range_mapping_current(request.json['category']['id'], new_sig_id)

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/yara_rules/<int:id>', methods=['PUT'])
@login_required
def update_yara_rule(id):
    do_not_bump_revision = request.json.get("do_not_bump_revision", False)

    entity = yara_rule.Yara_rule.query.get(id)
    if not entity:
        abort(404)

    if not do_not_bump_revision:
        db.session.add(yara_rule.Yara_rule_history(date_created=entity.date_created, revision=entity.revision,
                                                   rule_json=json.dumps(entity.to_revision_dict()),
                                                   user_id=current_user.id,
                                                   yara_rule_id=entity.id))

    if not entity.revision:
        entity.revision = 1

    temp_sig_id = entity.signature_id
    get_new_sig_id = False
    if request.json['category'] and 'category' in request.json['category'] and not entity.category == request.json['category']['category']:
        get_new_sig_id = True
        if not request.json['category']['current']:
            temp_sig_id = request.json['category']['range_min']
        else:
            temp_sig_id = request.json['category']['current'] + 1

        if temp_sig_id > request.json['category']['range_max']:
            abort(400)
    entity = yara_rule.Yara_rule(
        state=request.json['state']['state'] if request.json['state'] and 'state' in request.json['state'] else request.json['state'],
        name=request.json['name'],
        test_status=request.json.get('test_status', None),
        confidence=request.json['confidence'],
        severity=request.json['severity'],
        description=request.json['description'],
        category=request.json['category']['category'] if request.json['category'] and 'category' in request.json['category'] else request.json['category'],
        file_type=request.json['file_type'],
        subcategory1=request.json['subcategory1'],
        subcategory2=request.json['subcategory2'],
        subcategory3=request.json['subcategory3'],
        reference_link=request.json['reference_link'],
        reference_text=request.json['reference_text'],
        condition=yara_rule.Yara_rule.make_yara_sane(request.json["condition"], "condition:"),
        strings=yara_rule.Yara_rule.make_yara_sane(request.json["strings"], "strings:"),
        signature_id=temp_sig_id,
        id=id,
        modified_user_id=current_user.id,
        owner_user_id=request.json['owner_user']['id'] if request.json.get("owner_user", None) and request.json[
            "owner_user"].get("id", None) else None,
        revision=entity.revision if do_not_bump_revision else entity.revision + 1
    )
    db.session.merge(entity)
    db.session.commit()

    # THIS IS UGLY. FIGURE OUT WHY MERGE ISN'T WORKING
    entity = yara_rule.Yara_rule.query.get(entity.id)

    if get_new_sig_id:
        update_cfg_category_range_mapping_current(request.json['category']['id'], temp_sig_id)

    create_tags_mapping(entity.__tablename__, entity.id, request.json['addedTags'])
    delete_tags_mapping(entity.__tablename__, entity.id, request.json['removedTags'])

    return jsonify(entity.to_dict()), 200


@app.route('/ThreatKB/yara_rules/<int:id>', methods=['DELETE'])
@login_required
def delete_yara_rule(id):
    entity = yara_rule.Yara_rule.query.get(id)
    entity.active = False
    # tag_mapping_to_delete = entity.to_dict()['tags']

    if not entity:
        abort(404)
    db.session.merge(entity)
    db.session.commit()

    #delete_tags_mapping(entity.__tablename__, entity.id, tag_mapping_to_delete)

    return '', 204
