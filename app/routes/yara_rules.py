from app import app, db, auto, ENTITY_MAPPING
from app.routes import test_yara_rule
from app.models import yara_rule, cfg_states, comments
from flask import abort, jsonify, request, Response, json
from flask_login import current_user, login_required
import distutils

from app.models.metadata import Metadata, MetadataMapping
from app.routes.bookmarks import is_bookmarked, delete_bookmarks
from app.routes.cfg_category_range_mapping import update_cfg_category_range_mapping_current
from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping
from app.routes.comments import create_comment
from app.models.cfg_settings import Cfg_settings
from app.utilities import filter_entities

import datetime


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
        comments.Comments(comment=merged_into_comment, entity_type=ENTITY_MAPPING["SIGNATURE"],
                          entity_id=merge_from_yr.id, user_id=current_user.id))

    merged_from_comment = "The yara rule '%s' with event id '%s' was merged into this yara rule by '%s'" % (
        merge_from_yr.name, merge_from_yr.eventid, current_user.email)
    db.session.add(
        comments.Comments(comment=merged_from_comment, entity_type=ENTITY_MAPPING["SIGNATURE"],
                          entity_id=merge_to_yr.id, user_id=current_user.id))
    db.session.commit()

    delete_bookmarks(ENTITY_MAPPING["SIGNATURE"], merge_from_id, current_user.id)

    return get_yara_rule(merge_to_yr.id)


@app.route('/ThreatKB/yara_rules', methods=['GET'])
@auto.doc()
@login_required
def get_all_yara_rules():
    """Return a list of all yara_rule artifacts.

    include_merged: variable controlling whether merged signatures are returned, default False
    include_inactive: variable controlling whether inactive signatures are returned, default False

    Pagination variables:
    page_number: page number to start on, default 0
    page_size: the size of each page, default None (dont paginate)
    sort_by: column to sort by, must exist on the Yara_rule model, default None
    sort_direction: the direction to sort by if sorting, default ASC
    searches: dictionary of column filters as {column1:filter1, column2:filter2}, columns must exist on Yara_rule model, default {}

    Return: list of yara_rule artifact dictionaries"""
    include_inactive = request.args.get("include_inactive", False)
    include_yara_string = bool(distutils.util.strtobool(request.args.get("include_yara_string", "False")))
    short = bool(distutils.util.strtobool(request.args.get("short", "false")))
    include_metadata = bool(distutils.util.strtobool(request.args.get('include_metadata', "true")))

    if include_yara_string:
        include_yara_string = True

    include_merged = request.args.get('include_merged', False)
    searches = request.args.get('searches', '{}')
    page_number = request.args.get('page_number', False)
    page_size = request.args.get('page_size', False)
    sort_by = request.args.get('sort_by', False)
    sort_direction = request.args.get('sort_dir', 'ASC')
    exclude_totals = request.args.get('exclude_totals', False)

    response_dict = filter_entities(entity=yara_rule.Yara_rule,
                                    artifact_type=ENTITY_MAPPING["SIGNATURE"],
                                    searches=searches,
                                    page_number=page_number,
                                    page_size=page_size,
                                    sort_by=sort_by,
                                    sort_direction=sort_direction,
                                    include_metadata=include_metadata,
                                    exclude_totals=exclude_totals,
                                    default_sort="creation_date",
                                    include_inactive=include_inactive,
                                    include_merged=include_merged,
                                    include_yara_string=include_yara_string,
                                    short=short)

    return Response(response_dict, mimetype='application/json')


@app.route('/ThreatKB/yara_rules/<int:id>', methods=['GET'])
@auto.doc()
@login_required
def get_yara_rule(id):
    """Return yara_rule artifact associated with the given id
    Return: yara_rule artifact dictionary"""
    include_yara_string = request.args.get("include_yara_string", False)
    short = distutils.util.strtobool(request.args.get("short", "false"))

    if include_yara_string:
        include_yara_string = True

    entity = yara_rule.Yara_rule.query.get(id)
    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)

    return_dict = entity.to_dict(include_yara_string, short)
    return_dict["bookmarked"] = True if is_bookmarked(ENTITY_MAPPING["SIGNATURE"], id, current_user.id) \
        else False

    return jsonify(return_dict)


@app.route('/ThreatKB/yara_rules', methods=['POST'])
@auto.doc()
@login_required
def create_yara_rule():
    """Create yara_rule artifact
    From Data: name (str), state(str), category (str), condition (str), strings (str)
    Return: yara_rule artifact dictionary"""
    new_sig_id = 0

    release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
    draft_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_staging_state > 0).first()

    if not release_state or not draft_state:
        raise Exception("You must set a release, draft, and retirement state before modifying signatures")

    try:
        rule_state = request.json.get("state", None).get("state", None)
    except:
        rule_state = request.json.get("state", None)

    compile_on_save = Cfg_settings.get_setting("COMPILE_YARA_RULE_ON_SAVE")
    if compile_on_save and distutils.util.strtobool(compile_on_save) and (
            rule_state == release_state.state or rule_state == draft_state.state):
        test_result, return_code, stdout, stderr = test_yara_rule.does_rule_compile(request.json)
        if not test_result:
            raise Exception(
                "State submitted is " + str(
                    rule_state) + " and the rule could not be saved because it does not compile.\n\nerror_code=" + str(
                    return_code) + "\n\n" + stderr)

    if request.json['category'] and 'category' in request.json['category']:
        new_sig_id = request.json['category']['current'] + 1

    entity = yara_rule.Yara_rule(
        state=request.json['state']['state'] if 'state' in request.json['state'] else None,
        name=request.json['name'],
        description=request.json.get("description", None),
        references=request.json.get("references", None),
        category=request.json['category']['category'] if 'category' in request.json['category'] else None,
        condition=yara_rule.Yara_rule.make_yara_sane(request.json['condition'], "condition:"),
        strings=yara_rule.Yara_rule.make_yara_sane(request.json['strings'], "strings:"),
        eventid=new_sig_id,
        created_user_id=current_user.id,
        modified_user_id=current_user.id,
        owner_user_id=current_user.id,
        imports=yara_rule.Yara_rule.get_imports_from_string(request.json.get("imports", None))
    )

    if entity.state == release_state:
        entity.state = draft_state.state

    db.session.add(entity)
    db.session.commit()

    entity.tags = create_tags_mapping(entity.__tablename__, entity.id, request.json['tags'])

    if request.json.get('new_comment', None):
        create_comment(request.json['new_comment'],
                       ENTITY_MAPPING["SIGNATURE"],
                       entity.id,
                       current_user.id)

    if new_sig_id > 0:
        update_cfg_category_range_mapping_current(request.json['category']['id'], new_sig_id)

    dirty = False
    for name, value_dict in request.json.get("metadata_values", {}).iteritems():
        if not name or not value_dict:
            continue

        m = db.session.query(MetadataMapping).join(Metadata, Metadata.id == MetadataMapping.metadata_id).filter(
            Metadata.key == name).filter(Metadata.artifact_type == ENTITY_MAPPING["SIGNATURE"]).filter(
            MetadataMapping.artifact_id == entity.id).first()
        if m:
            m.value = value_dict["value"]
            db.session.add(m)
            dirty = True
        else:
            m = db.session.query(Metadata).filter(Metadata.key == name).filter(
                Metadata.artifact_type == ENTITY_MAPPING["SIGNATURE"]).first()
            db.session.add(MetadataMapping(value=value_dict["value"], metadata_id=m.id, artifact_id=entity.id,
                                           created_user_id=current_user.id))
            dirty = True

    if dirty:
        db.session.commit()

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/yara_rules/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
def update_yara_rule(id):
    """Update yara_rule artifact
    From Data: name (str), state(str), category (str), condition (str), strings (str)
    Return: yara_rule artifact dictionary"""
    do_not_bump_revision = request.json.get("do_not_bump_revision", False)

    entity = yara_rule.Yara_rule.query.get(id)

    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)

    release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
    draft_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_staging_state > 0).first()
    old_state = entity.state

    try:
        rule_state = request.json.get("state", None).get("state", None)
    except:
        rule_state = request.json.get("state", None)

    compile_on_save = Cfg_settings.get_setting("COMPILE_YARA_RULE_ON_SAVE")
    if compile_on_save and distutils.util.strtobool(compile_on_save) and (
            rule_state == release_state.state or rule_state == draft_state.state):
        test_result, return_code, stdout, stderr = test_yara_rule.does_rule_compile(request.json)
        if not test_result:
            raise Exception(
                "State submitted is " + str(
                    rule_state) + " and the rule could not be saved because it does not compile.\n\nerror_code=" + str(
                    return_code) + "\n\n" + stderr)

    if not release_state or not draft_state:
        raise Exception("You must set a release, draft, and retirement state before modifying signatures")

    if not do_not_bump_revision:
        db.session.add(yara_rule.Yara_rule_history(date_created=datetime.datetime.now(), revision=entity.revision,
                                                   rule_json=json.dumps(entity.to_revision_dict()),
                                                   user_id=current_user.id,
                                                   yara_rule_id=entity.id,
                                                   state=entity.state))

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
        description=request.json.get("description", None),
        references=request.json.get("references", None),
        category=request.json['category']['category'] if request.json['category'] and 'category' in request
            .json['category'] else request.json['category'],
        condition=yara_rule.Yara_rule.make_yara_sane(request.json["condition"], "condition:"),
        strings=yara_rule.Yara_rule.make_yara_sane(request.json["strings"], "strings:"),
        eventid=temp_sig_id,
        id=id,
        created_user_id=entity.created_user_id,
        creation_date=entity.creation_date,
        modified_user_id=current_user.id,
        last_revision_date=datetime.datetime.now(),
        owner_user_id=request.json['owner_user']['id'] if request.json.get("owner_user", None) and request
            .json["owner_user"].get("id", None) else None,
        revision=entity.revision if do_not_bump_revision else entity.revision + 1,
        imports=yara_rule.Yara_rule.get_imports_from_string(request.json.get("imports", None))
    )

    if old_state == release_state.state and entity.state == release_state.state and not do_not_bump_revision:
        entity.state = draft_state.state

    db.session.merge(entity)
    db.session.commit()

    dirty = False
    for name, value_dict in request.json.get("metadata_values", {}).iteritems():
        if not name or not value_dict:
            continue

        m = db.session.query(MetadataMapping).join(Metadata, Metadata.id == MetadataMapping.metadata_id).filter(
            Metadata.key == name).filter(Metadata.artifact_type == ENTITY_MAPPING["SIGNATURE"]).filter(
            MetadataMapping.artifact_id == entity.id).first()
        if m:
            m.value = value_dict["value"]
            db.session.add(m)
            dirty = True
        else:
            m = db.session.query(Metadata).filter(Metadata.key == name).filter(
                Metadata.artifact_type == ENTITY_MAPPING["SIGNATURE"]).first()
            db.session.add(MetadataMapping(value=value_dict["value"], metadata_id=m.id, artifact_id=entity.id,
                                           created_user_id=current_user.id))
            dirty = True

    if dirty:
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
    delete_bookmarks(ENTITY_MAPPING["SIGNATURE"], id, current_user.id)

    return jsonify(''), 204
