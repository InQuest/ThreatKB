from app import app, db, auto
from app.models import yara_rule, cfg_states, comments
from flask import abort, jsonify, request, Response, json
from flask.ext.login import current_user, login_required

from app.models.bookmarks import Bookmarks
from app.routes.bookmarks import is_bookmarked, delete_bookmarks
from app.routes.cfg_category_range_mapping import update_cfg_category_range_mapping_current
from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping


@app.route('/ThreatKB/yara_rules/merge_signatures', methods=['POST'])
@auto.doc()
@login_required
def merge_signatures():
    """Merge a signature into another
    From Data: merge_from_id (int), merge_to_id (int)
    Return: merged yara_rule artifact dictionary"""
    merge_from_id = request.json.get("merge_from_id", None)
    merge_to_id = request.json.get("merge_to_id", None)

    if not merge_from_id or not merge_to_id:
        abort(412, description="Not enough info provided")

    merge_from_yr = yara_rule.Yara_rule.query.filter_by(id=merge_from_id).first()
    merge_to_yr = yara_rule.Yara_rule.query.filter_by(id=merge_to_id).first()

    merged_state = "Merged"
    if not cfg_states.Cfg_states.query.filter_by(state=merged_state).first():
        db.session.add(cfg_states.Cfg_states(state=merged_state))
        db.session.commit()

    merge_from_yr.state = merged_state
    db.session.add(merge_from_yr)
    merged_into_comment = "This yara rule was merged into signature '%s' with event id '%s' by '%s'" % (
        merge_to_yr.name, merge_to_yr.eventid, current_user.email)
    db.session.add(
        comments.Comments(comment=merged_into_comment, entity_type=comments.Comments.ENTITY_MAPPING["SIGNATURE"],
                          entity_id=merge_from_yr.id, user_id=current_user.id))

    merged_from_comment = "The yara rule '%s' with event id '%s' was merged into this yara rule by '%s'" % (
        merge_from_yr.name, merge_from_yr.eventid, current_user.email)
    db.session.add(
        comments.Comments(comment=merged_from_comment, entity_type=comments.Comments.ENTITY_MAPPING["SIGNATURE"],
                          entity_id=merge_to_yr.id, user_id=current_user.id))
    db.session.commit()

    delete_bookmarks(Bookmarks.ENTITY_MAPPING["SIGNATURE"], merge_from_id, current_user.id)

    return get_yara_rule(merge_to_yr.id)


@app.route('/ThreatKB/yara_rules', methods=['GET'])
@auto.doc()
@login_required
def get_all_yara_rules():
    """Return a list of all yara_rule artifacts.
    Return: list of yara_rule artifact dictionaries"""
    include_inactive = request.args.get("include_inactive", False)
    include_merged = request.args.get('include_merged', False)
    searches = request.args.get('searches', '{}')
    page_number = request.args.get('page_number', False)
    page_size = request.args.get('page_size', False)
    sort_by = request.args.get('sort_by', False)
    sort_direction = request.args.get('sort_dir', 'ASC')

    entities = yara_rule.Yara_rule.query

    if not current_user.admin:
        entities = entities.filter_by(owner_user_id=current_user.id)

    if not include_inactive:
        entities = entities.filter_by(active=True)

    searches = json.loads(searches)
    for column, value in searches.items():
        try:
            column = getattr(yara_rule.Yara_rule, column)
            entities = entities.filter(column.like("%" + str(value) + "%"))
        except:
            continue

    if not include_merged:
        entities = entities.filter(yara_rule.Yara_rule.state != 'Merged')

    filtered_entities = entities
    total_count = entities.count()

    if sort_by:
        filtered_entities = filtered_entities.order_by("%s %s" % (sort_by, sort_direction))

    if page_size:
        filtered_entities = filtered_entities.limit(int(page_size))

    if page_number:
        filtered_entities = filtered_entities.offset(int(page_number) * int(page_size))

    filtered_entities = filtered_entities.all()

    response_dict = dict()
    response_dict['data'] = [entity.to_dict() for entity in filtered_entities]
    response_dict['total_count'] = total_count

    return Response(json.dumps(response_dict), mimetype='application/json')


@app.route('/ThreatKB/yara_rules/<int:id>', methods=['GET'])
@auto.doc()
@login_required
def get_yara_rule(id):
    """Return yara_rule artifact associated with the given id
    Return: yara_rule artifact dictionary"""
    entity = yara_rule.Yara_rule.query.get(id)
    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)

    return_dict = entity.to_dict()
    return_dict["bookmarked"] = True if is_bookmarked(Bookmarks.ENTITY_MAPPING["SIGNATURE"], id, current_user.id)\
        else False

    return jsonify(return_dict)


@app.route('/ThreatKB/yara_rules', methods=['POST'])
@auto.doc()
@login_required
def create_yara_rule():
    """Create yara_rule artifact
    From Data: name (str), test_status (str), confidence (int), severity (int), description (str), state(str), category (str), file_type (str), subcategory1 (str), subcategory2 (str), subcategory3 (str), reference_link (str), condition (str), strings (str)
    Return: yara_rule artifact dictionary"""
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
        , condition=yara_rule.Yara_rule.make_yara_sane(request.json['condition'], "condition:")
        , strings=yara_rule.Yara_rule.make_yara_sane(request.json['strings'], "strings:")
        , eventid=new_sig_id
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
@auto.doc()
@login_required
def update_yara_rule(id):
    """Update yara_rule artifact
    From Data: name (str), test_status (str), confidence (int), severity (int), description (str), state(str), category (str), file_type (str), subcategory1 (str), subcategory2 (str), subcategory3 (str), reference_link (str), reference_text (str), condition (str), strings (str)
    Return: yara_rule artifact dictionary"""
    do_not_bump_revision = request.json.get("do_not_bump_revision", False)

    entity = yara_rule.Yara_rule.query.get(id)
    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)

    if not do_not_bump_revision:
        db.session.add(yara_rule.Yara_rule_history(date_created=entity.creation_date, revision=entity.revision,
                                                   rule_json=json.dumps(entity.to_revision_dict()),
                                                   user_id=current_user.id,
                                                   yara_rule_id=entity.id))

    if not entity.revision:
        entity.revision = 1

    temp_sig_id = entity.eventid
    get_new_sig_id = False
    if request.json['category'] and 'category' in request.json['category'] and not entity.category == \
            request.json['category']['category']:
        get_new_sig_id = True
        if not request.json['category']['current']:
            temp_sig_id = request.json['category']['range_min']
        else:
            temp_sig_id = request.json['category']['current'] + 1

        if temp_sig_id > request.json['category']['range_max']:
            abort(400)
    entity = yara_rule.Yara_rule(
        state=request.json['state']['state'] if request.json['state'] and 'state' in request.json['state'] else
        request.json['state'],
        name=request.json['name'],
        test_status=request.json.get('test_status', None),
        confidence=request.json['confidence'],
        severity=request.json['severity'],
        description=request.json['description'],
        category=request.json['category']['category'] if request.json['category'] and 'category' in request
            .json['category'] else request.json['category'],
        file_type=request.json['file_type'],
        subcategory1=request.json['subcategory1'],
        subcategory2=request.json['subcategory2'],
        subcategory3=request.json['subcategory3'],
        reference_link=request.json['reference_link'],
        condition=yara_rule.Yara_rule.make_yara_sane(request.json["condition"], "condition:"),
        strings=yara_rule.Yara_rule.make_yara_sane(request.json["strings"], "strings:"),
        eventid=temp_sig_id,
        id=id,
        modified_user_id=current_user.id,
        owner_user_id=request.json['owner_user']['id'] if request.json.get("owner_user", None) and request
            .json["owner_user"].get("id", None) else None,
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
@auto.doc()
@login_required
def delete_yara_rule(id):
    """INACTIVATE yara_rule artifact associated with id
    Return: None"""
    entity = yara_rule.Yara_rule.query.get(id)
    entity.active = False
    # tag_mapping_to_delete = entity.to_dict()['tags']

    if not entity:
        abort(404)

    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)

    db.session.merge(entity)
    db.session.commit()

    # delete_tags_mapping(entity.__tablename__, entity.id, tag_mapping_to_delete)
    delete_bookmarks(Bookmarks.ENTITY_MAPPING["SIGNATURE"], id, current_user.id)

    return jsonify(''), 204
