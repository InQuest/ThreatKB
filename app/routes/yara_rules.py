from app import app, db, auto, ENTITY_MAPPING
from app.models.yara_rule import Yara_rule_history, Yara_rule
from app.models.cfg_states import Cfg_states
from app.routes import test_yara_rule
from app.models import yara_rule, cfg_states, comments
from flask import abort, jsonify, request, Response, json
from flask_login import current_user, login_required
import distutils
from app.utilities import extract_yara_rules_text, extract_artifacts_text
from app.models.metadata import Metadata, MetadataMapping
from app.models.releases import get_release_yara_rule_history_mapping, get_release_metadata
from app.routes.batch import batch_update, batch_delete
from app.routes.bookmarks import is_bookmarked, delete_bookmarks
from app.routes.cfg_category_range_mapping import update_cfg_category_range_mapping_current
from app.routes.tags_mapping import create_tags_mapping, delete_tags_mapping, get_tags_for_source, \
    batch_delete_tags_mapping_for_source_id
from app.routes.comments import create_comment
from app.models.cfg_settings import Cfg_settings
from app.utilities import filter_entities
import datetime
import uuid
import random
import string
import base64


@app.route('/ThreatKB/yara_rules/merge_signatures', methods=['POST'])
def merge_signatures():
    signatures = request.json.get('signatures', [])
    save_output = request.json.get('save_output', 0)
    signature_ids = request.json.get('signature_ids', [])

    for i in range(len(signatures)):
        try:
            signatures[i] = base64.b64decode(signatures[i]).decode()
        except:
            pass

    if signature_ids and (not current_user.is_authenticated or not current_user.active or not current_user.admin):
        abort(403)

    for id_ in signature_ids:
        signature = db.session.query(yara_rule.Yara_rule).filter(yara_rule.Yara_rule.id == id_).first()
        if signature:
            signatures.append(signature.to_dict(include_yara_rule_string=True)['yara_rule_string'])

    if not signatures or not type(signatures) == list or len(signatures) < 2:
        abort(412, description="You must provide at least 2 signatures as a list")

    rules = extract_yara_rules_text("\n\n".join(signatures))
    rule_name = f"Merged_Rule_{str(uuid.uuid4())[:8]}"
    description = f"\"Merger of {', '.join([rule['parsed_rule']['rule_name'] for rule in rules])}\""
    strings = ""
    condition = ""
    imports = ""
    r = 1
    for rule in rules:
        old_new = {}
        current_strings = []
        postfix = f"r{r}"
        for s in rule['parsed_rule']['strings']:
            old_name = s['name'].strip()
            if old_name.startswith('$'):
                name = f"${s['name'].strip()[1:]}_{postfix}"
            else:
                name = f"{s['name'].strip()}_{postfix}"

            if s['value'].startswith("{") or s['value'].startswith("/"):
                value = s['value'].strip()
            else:
                value = f"\"{s['value'].strip()}\""

            old_new[old_name] = name
            modifier = ' '.join(s.get('modifiers', []))
            current_strings.append(
                f"{name} = {value} {modifier}"
            )
        strings += '\n\t\t' + '\n\t\t'.join(current_strings)
        app.logger.info(f"condition is\n{rule['condition']}")
        this_condition = rule['condition'].strip()
        for old, new in old_new.items():
            this_condition = this_condition.replace(old, new)
        condition += f"(\n\t{this_condition}\n\t)\n\tor\n\t"
        imports += rule['imports'] + "\n" if not rule['imports'] in imports else ""
        r += 1

    condition = condition.rstrip("\n\tor\n\t")
    full_rule = f"""
    {imports}

    rule {rule_name}
    {{
        meta:
            description = {description}
        strings:{strings}
        condition:
            {condition}
    }}
    """

    app.logger.info(f"rule is\n{full_rule}")
    if not save_output:
        return jsonify({"merged_signature": full_rule.strip(" ").strip()})
    else:
        if not current_user.is_authenticated or not current_user.active or not current_user.admin:
            abort(403)
        output = extract_artifacts_text(do_extract_ip=False,
                                        do_extract_dns=False,
                                        do_extract_signature=True,
                                        text=full_rule)
        rule_dict = output[0]
        yr, fta = yara_rule.Yara_rule.get_yara_rule_from_yara_dict(rule_dict, {})
        yr.created_user_id, yr.modified_user_id = current_user.id, current_user.id
        staging_state = db.session.query(Cfg_states).filter(Cfg_states.is_staging_state > 0).first()
        yr.state = staging_state.state
        yr.description = description.strip('"')
        yr.revision = 1
        db.session.add(yr)
        db.session.commit()
        return jsonify(yr.to_dict()), 201


@app.route('/ThreatKB/yara_rules/merge_signatures_by_id', methods=['POST'])
@auto.doc()
@login_required
def merge_signatures_by_id():
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

    view = request.args.get("view", "Active Only")

    if view == "All":
        include_inactive = True
        include_active = True
    elif view == "Active Only":
        include_inactive = False
        include_active = True
    elif view == "Inactive Only":
        include_inactive = True
        include_active = False
    else:
        include_inactive = False
        include_active = True

    include_yara_string = bool(distutils.util.strtobool(request.args.get("include_yara_string", "False")))
    short = bool(distutils.util.strtobool(request.args.get("short", "false")))
    include_metadata = bool(distutils.util.strtobool(request.args.get('include_metadata', "true")))
    include_tags = bool(distutils.util.strtobool(request.args.get('include_tags', "true")))
    include_comments = bool(distutils.util.strtobool(request.args.get('include_comments', "true")))


    if include_yara_string:
        include_yara_string = True

    include_merged = request.args.get('include_merged', False)
    searches = request.args.get('searches', '{}')
    page_number = request.args.get('page_number', False)
    page_size = request.args.get('page_size', False)
    sort_by = request.args.get('sort_by', False)
    operator = request.args.get('operator', 'and')
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
                                    include_tags=include_tags,
                                    include_comments=include_comments,
                                    include_active=include_active,
                                    include_merged=include_merged,
                                    include_yara_string=include_yara_string,
                                    short=short,
                                    operator=operator)

    return Response(response_dict, mimetype='application/json')


@app.route('/ThreatKB/yara_rules/<int:id>', methods=['GET'])
@auto.doc()
@login_required
def get_yara_rule(id):
    """Return yara_rule artifact associated with the given id
    Return: yara_rule artifact dictionary"""
    include_yara_string = request.args.get("include_yara_string", False)
    include_revisions = request.args.get("include_revisions", True)
    include_metadata = request.args.get("include_metadata", True)
    short = distutils.util.strtobool(request.args.get("short", "false"))

    if include_yara_string:
        include_yara_string = True

    entity = yara_rule.Yara_rule.query.get(id)
    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)

    return_dict = entity.to_dict(include_yara_string, short, include_revisions, include_metadata)
    return_dict["bookmarked"] = True if is_bookmarked(ENTITY_MAPPING["SIGNATURE"], id, current_user.id) \
        else False

    return jsonify(return_dict)


@app.route('/ThreatKB/yara_rules/<int:id>/release_mapping', methods=['GET'])
@auto.doc()
@login_required
def get_yara_rule_release_mapping(id):
    """Return yara_rule artifact associated with the given id
    Return: yara_rule artifact dictionary"""

    entity = yara_rule.Yara_rule.query.get(id)
    if not entity:
        abort(404)
    if not current_user.admin and entity.owner_user_id != current_user.id:
        abort(403)

    rule_history = db.session.query(Yara_rule_history.id).filter(Yara_rule_history.yara_rule_id == entity.id).all()
    if not rule_history:
        return jsonify([])

    release_mapping = get_release_yara_rule_history_mapping()
    release_metadata = get_release_metadata()
    mapping = {}
    for rh in rule_history:
        if not rh.id in mapping:
            mapping[rh.id] = []
        if rh.id in release_mapping:
            for release_id in release_mapping[rh.id]:
                mapping[rh.id].append(release_metadata[release_id])

    return_mapping = {}
    for key, val in mapping.items():
        return_mapping[int(key)] = ",".join([release["name"] for release in val])
    return jsonify(return_mapping)


@app.route('/ThreatKB/yara_rules/<int:yara_rule_id>/revision/<int:revision>', methods=['GET'])
@auto.doc()
@login_required
def get_yara_rule_string_from_revision(yara_rule_id, revision):
    """Return yara_rule string associated with the given yara rule and revision number
    Return: yara_rule string representation"""

    current_entity = yara_rule.Yara_rule.query.get(yara_rule_id)
    revision_entity = Yara_rule_history.query \
        .filter_by(yara_rule_id=yara_rule_id) \
        .filter_by(revision=revision) \
        .first()

    if not current_entity or not revision_entity:
        abort(404)

    if not current_user.admin and current_entity.owner_user_id != current_user.id:
        abort(403)

    revision_dict = revision_entity.to_dict()
    yara_revision_dict = revision_dict["rule_json"]
    yara_rule_string = Yara_rule.to_yara_rule_string(yara_revision_dict)

    return jsonify(yara_rule_string)


@app.route('/ThreatKB/yara_rules', methods=['POST', 'PUT'])
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

    unique_rule_name_enforcement = Cfg_settings.get_setting("ENFORCE_UNIQUE_YARA_RULE_NAMES")
    if unique_rule_name_enforcement and distutils.util.strtobool(unique_rule_name_enforcement):
        if db.session.query(yara_rule.Yara_rule).filter(yara_rule.Yara_rule.name == request.json['name']).first():
            raise Exception("You cannot save two rules with the same name.")

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
        imports=yara_rule.Yara_rule.get_imports_from_string(request.json.get("imports", None)),
        active=request.json.get("active", True)
    )

    mitre_techniques = Cfg_settings.get_setting("MITRE_TECHNIQUES").split(",")
    entity.mitre_techniques = request.json.get("mitre_techniques", [])
    matches = [technique for technique in entity.mitre_techniques if technique not in mitre_techniques]
    if matches:
        raise Exception

    mitre_tactics = Cfg_settings.get_setting("MITRE_TACTICS").split(",")
    entity.mitre_tactics = request.json.get("mitre_tactics", [])
    matches = [tactic for tactic in entity.mitre_tactics if tactic not in mitre_tactics]
    if matches:
        raise Exception

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
    for name, value_dict in request.json.get("metadata_values", {}).items():
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

    db.session.add(yara_rule.Yara_rule_history(date_created=datetime.datetime.now(),
                                               revision=entity.revision,
                                               rule_json=json.dumps(entity.to_revision_dict()),
                                               user_id=current_user.id,
                                               yara_rule_id=entity.id,
                                               state=entity.state))
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/yara_rules/activate/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
def activate_yara_rule(id):
    entity = yara_rule.Yara_rule.query.get(id)
    entity.active = 1
    db.session.merge(entity)
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

    unique_rule_name_enforcement = Cfg_settings.get_setting("ENFORCE_UNIQUE_YARA_RULE_NAMES")
    if unique_rule_name_enforcement and distutils.util.strtobool(unique_rule_name_enforcement):
        if any([True for rule in
                db.session.query(yara_rule.Yara_rule).filter(yara_rule.Yara_rule.name == request.json['name']).all() if
                not rule.id == id]):
            raise Exception("You cannot save two rules with the same name.")

    if not release_state or not draft_state:
        raise Exception("You must set a release, draft, and retirement state before modifying signatures")

    compile_on_save = Cfg_settings.get_setting("COMPILE_YARA_RULE_ON_SAVE")
    if compile_on_save and distutils.util.strtobool(compile_on_save) and (
            rule_state == release_state.state or rule_state == draft_state.state):
        test_result, return_code, stdout, stderr = test_yara_rule.does_rule_compile(request.json)
        if not test_result:
            raise Exception(
                "State submitted is " + str(
                    rule_state) + " and the rule could not be saved because it does not compile.\n\nerror_code=" + str(
                    return_code) + "\n\n" + str(stderr))

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
        imports=yara_rule.Yara_rule.get_imports_from_string(request.json.get("imports", None)),
        active=request.json.get("active", entity.active)
    )

    mitre_techniques = Cfg_settings.get_setting("MITRE_TECHNIQUES").split(",")
    entity.mitre_techniques = request.json.get("mitre_techniques", [])
    matches = [technique for technique in entity.mitre_techniques if technique not in mitre_techniques]
    if matches:
        raise Exception

    mitre_sub_techniques = Cfg_settings.get_setting("MITRE_SUB_TECHNIQUES").split(",")
    entity.mitre_sub_techniques = request.json.get("mitre_sub_techniques", [])
    matches = [technique for technique in entity.mitre_sub_techniques if technique not in mitre_sub_techniques]
    if matches:
        raise Exception

    mitre_tactics = Cfg_settings.get_setting("MITRE_TACTICS").split(",")
    entity.mitre_tactics = request.json.get("mitre_tactics", [])
    matches = [tactic for tactic in entity.mitre_tactics if tactic not in mitre_tactics]
    if matches:
        raise Exception

    if old_state == release_state.state and entity.state == release_state.state and not do_not_bump_revision:
        entity.state = draft_state.state

    db.session.merge(entity)
    db.session.commit()

    dirty = False
    for name, value_dict in request.json.get("metadata_values", {}).items():
        if not name or not value_dict:
            continue

        m = db.session.query(MetadataMapping, Metadata).join(Metadata, Metadata.id == MetadataMapping.metadata_id).filter(
            Metadata.key == name).filter(Metadata.artifact_type == ENTITY_MAPPING["SIGNATURE"]).filter(
            MetadataMapping.artifact_id == entity.id).first()
        if m and m[0]:
            m[0].value = value_dict.get("value", None) if not m[1].required else value_dict["value"]
            db.session.add(m[0])
            dirty = True
        else:
            m = db.session.query(Metadata).filter(Metadata.key == name).filter(
                Metadata.artifact_type == ENTITY_MAPPING["SIGNATURE"]).first()
            db.session.add(MetadataMapping(value=value_dict["value"] if m.required else value_dict.get("value", None), metadata_id=m.id, artifact_id=entity.id,
                                           created_user_id=current_user.id))
            dirty = True

    if dirty:
        db.session.commit()

    # THIS IS UGLY. FIGURE OUT WHY MERGE ISN'T WORKING
    entity = yara_rule.Yara_rule.query.get(entity.id)

    if not do_not_bump_revision:
        db.session.add(yara_rule.Yara_rule_history(date_created=datetime.datetime.now(), revision=entity.revision,
                                                   rule_json=json.dumps(entity.to_revision_dict()),
                                                   user_id=current_user.id,
                                                   yara_rule_id=entity.id,
                                                   state=entity.state))

    if get_new_sig_id:
        update_cfg_category_range_mapping_current(request.json['category']['id'], temp_sig_id)

    current_tags = get_tags_for_source(entity.__tablename__, entity.id)
    new_tags = request.json['tags']
    tags_to_delete, tags_to_create = [c_tag for c_tag in current_tags if c_tag not in new_tags], [n_tag for n_tag in
                                                                                                  new_tags if
                                                                                                  n_tag not in current_tags]
    if tags_to_delete:
        batch_delete_tags_mapping_for_source_id(entity.__tablename__, entity.id, [tag['id'] for tag in tags_to_delete])
    if tags_to_create:
        create_tags_mapping(entity.__tablename__, entity.id, tags_to_create)

    return jsonify(entity.to_dict(include_yara_rule_string=True)), 200


@app.route('/ThreatKB/yara_rules/batch/edit', methods=['PUT'])
@auto.doc()
@login_required
def batch_update_yara_rules():
    """Batch update yara rules artifacts
    From Data: batch {
                 state (str),
                 owner_user (str),
                 tags (array),
                 ids (array)
               }
    Return: Success Code"""

    if 'batch' in request.json and request.json['batch']:
        return batch_update(batch=request.json['batch'],
                            artifact=yara_rule.Yara_rule,
                            session=db.session)


@app.route('/ThreatKB/yara_rules/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
def delete_yara_rule(id):
    """INACTIVATE yara_rule artifact associated with id
    Return: None"""
    entity = yara_rule.Yara_rule.query.get(id)

    if entity.active:
        entity.active = False

        if not entity:
            abort(404)

        if not current_user.admin and entity.owner_user_id != current_user.id:
            abort(403)

        db.session.merge(entity)
        db.session.commit()

        # delete_tags_mapping(entity.__tablename__, entity.id)
        delete_bookmarks(ENTITY_MAPPING["SIGNATURE"], id, current_user.id)
    else:

        db.session.query(yara_rule.Yara_testing_history).filter(
            yara_rule.Yara_testing_history.yara_rule_id.in_([entity.id])).delete(synchronize_session='fetch')
        db.session.query(yara_rule.Yara_rule_history).filter(
            yara_rule.Yara_rule_history.yara_rule_id.in_([entity.id])).delete(synchronize_session='fetch')
        db.session.delete(entity)
        db.session.commit()

        delete_bookmarks(ENTITY_MAPPING["SIGNATURE"], id, current_user.id)

    return jsonify(''), 204


@app.route('/ThreatKB/yara_rules/batch/delete', methods=['PUT'])
@auto.doc()
@login_required
def batch_delete_yara_rules():
    """Batch inactivate yara rules artifacts
    From Data: batch {
                 ids (array)
               }
    Return: Success Code"""

    if 'batch' in request.json and request.json['batch']:
        return batch_delete(batch=request.json['batch'],
                            artifact=yara_rule.Yara_rule,
                            session=db.session,
                            entity_mapping=ENTITY_MAPPING["SIGNATURE"],
                            is_yara=True)


@app.route('/ThreatKB/yara_rules/copy', methods=['POST'])
@auto.doc()
@login_required
def copy_yara_rules():
    """Get yara strings for copy
    From Data: ids (array)
    Return: yara strings for copy"""

    signatures = []
    if 'copy' in request.json and request.json['copy']\
            and 'ids' in request.json['copy'] and request.json['copy']['ids']:
        for sig_id in request.json['copy']['ids']:
            sig = yara_rule.Yara_rule.query.get(sig_id)
            if not sig:
                abort(404)
            if not current_user.admin and sig.owner_user_id != current_user.id:
                abort(403)

            signatures.append(sig.to_dict(include_yara_rule_string=True)["yara_rule_string"])

    return jsonify('\n\n'.join(map(str, signatures))), 200


@app.route('/ThreatKB/yara_rules/delete_all_inactive', methods=['PUT'])
@auto.doc()
@login_required
def delete_all_inactive_yara_rules():
    rules_to_delete = db.session.query(yara_rule.Yara_rule).filter(yara_rule.Yara_rule.active == 0).all()
    rules_to_delete_ids = [rule.id for rule in rules_to_delete]
    db.session.query(yara_rule.Yara_testing_history).filter(
        yara_rule.Yara_testing_history.yara_rule_id.in_(rules_to_delete_ids)).delete(synchronize_session='fetch')
    db.session.query(yara_rule.Yara_rule_history).filter(
        yara_rule.Yara_rule_history.yara_rule_id.in_(rules_to_delete_ids)).delete(synchronize_session='fetch')
    db.session.query(yara_rule.Yara_rule).filter(yara_rule.Yara_rule.active == 0).delete()
    db.session.commit()
    return jsonify(''), 200
