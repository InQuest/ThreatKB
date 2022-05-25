from flask import abort, jsonify, request
from flask_login import login_required, current_user
from app import app, db, admin_only, auto, ENTITY_MAPPING
from app.models import c2ip, c2dns, yara_rule, cfg_states, comments, cfg_settings
from app.models.metadata import Metadata
from app.utilities import extract_artifacts
import distutils
from app.models.whitelist import Whitelist
import datetime
import json


#####################################################################

def save_artifacts(extract_ip, extract_dns, extract_signature, artifacts, shared_reference=None,
                   shared_description=None, shared_state=None, shared_owner=None, metadata_field_mapping={}):
    default_state = "Imported"
    return_artifacts = []
    duplicate_artifacts = []
    fields_to_add = {}
    metadata_to_save_ip = []
    metadata_to_save_dns = []
    error_artifacts = []

    domain_names = {domain_name.domain_name.lower(): domain_name for domain_name in c2dns.C2dns.query.all()}
    ip_addresses = {ipaddress.ip: ipaddress for ipaddress in c2ip.C2ip.query.all()}
    yara_rules = {yr.name: yr for yr in db.session.query(yara_rule.Yara_rule).all()}
    unique_rule_name_enforcement = cfg_settings.Cfg_settings.get_setting("ENFORCE_UNIQUE_YARA_RULE_NAMES")

    if not cfg_states.Cfg_states.query.filter_by(state=default_state).first():
        db.session.add(cfg_states.Cfg_states(state=default_state))
        db.session.commit()

    for artifact in artifacts:
        try:
            if artifact["type"].lower() == "ip" and extract_ip:

                # old_ip = c2ip.C2ip.query.filter(c2ip.C2ip.ip == artifact["artifact"]).first()
                old_ip = ip_addresses.get(artifact["artifact"], None)
                if old_ip:
                    message = "System comment: duplicate IP '%s' found at '%s' by '%s'" % (
                    artifact["artifact"], shared_reference if shared_reference else "no reference provided",
                    current_user.email)
                    db.session.add(
                        comments.Comments(comment=message, entity_type=ENTITY_MAPPING["IP"],
                                          entity_id=old_ip.id, user_id=current_user.id))
                    duplicate_artifacts.append(artifact)
                    continue
                else:
                    ip = c2ip.C2ip.get_c2ip_from_ip(artifact, metadata_field_mapping)
                    ip.created_user_id, ip.modified_user_id = current_user.id, current_user.id
                    ip.state = default_state if not shared_state else shared_state
                    if Whitelist.hits_whitelist(ip.ip, ip.state):
                        error_artifacts.append((ip.ip, f"Whitelist validation failed {ip.ip}"))
                        continue

                    if shared_reference:
                        ip.references = shared_reference

                    if shared_description:
                        ip.description = shared_description

                    if shared_owner:
                        ip.owner_user_id = shared_owner

                    if artifact.get("metadata"):
                        metadata_to_save_ip.append((ip, artifact["metadata"]))

                    db.session.add(ip)
                    db.session.commit()
                    return_artifacts.append(ip)
            elif artifact["type"].lower() in ["dns", "domain_name"] and extract_dns:
                # old_dns = c2dns.C2dns.query.filter(c2dns.C2dns.domain_name == artifact["artifact"]).first()
                old_dns = domain_names.get(artifact["artifact"].lower(), None)
                if old_dns:
                    message = "System comment: duplicate DNS '%s' found at '%s' by '%s'" % (
                    artifact["artifact"], shared_reference if shared_reference else "no reference provided",
                    current_user.email)
                    db.session.add(
                        comments.Comments(comment=message, entity_type=ENTITY_MAPPING["DNS"],
                                          entity_id=old_dns.id, user_id=current_user.id))
                    duplicate_artifacts.append(artifact)
                    continue
                else:
                    dns = c2dns.C2dns.get_c2dns_from_hostname(artifact, metadata_field_mapping)
                    dns.created_user_id, dns.modified_user_id = current_user.id, current_user.id
                    dns.state = default_state if not shared_state else shared_state
                    if Whitelist.hits_whitelist(dns.domain_name, dns.state):
                        error_artifacts.append((dns.domain_name, f"Whitelist validation failed {dns.domain_name}"))
                        continue

                    if shared_reference:
                        dns.references = shared_reference
                    if shared_description:
                        dns.description = shared_description
                    if shared_state:
                        dns.state = shared_state
                    if shared_owner:
                        dns.owner_user_id = shared_owner

                    if artifact.get("metadata", None):
                        metadata_to_save_dns.append((dns, artifact["metadata"]))

                    db.session.add(dns)
                    db.session.commit()
                    return_artifacts.append(dns)
            elif artifact["type"].lower() == "yara_rule" and extract_signature:
                yr = yara_rules.get(artifact["rule"]["rule_name"], None)
                if unique_rule_name_enforcement and yr:
                    duplicate_artifacts.append(artifact)
                    continue

                yr, fta = yara_rule.Yara_rule.get_yara_rule_from_yara_dict(artifact, metadata_field_mapping)
                yr.created_user_id, yr.modified_user_id = current_user.id, current_user.id
                yr.state = default_state if not shared_state else shared_state
                yr.revision = 1
                if shared_reference:
                    yr.references = shared_reference
                if shared_description:
                    yr.description = shared_description
                if shared_owner:
                    yr.owner_user_id = shared_owner

                db.session.add(yr)
                db.session.commit()
                db.session.add(yara_rule.Yara_rule_history(date_created=datetime.datetime.now(),
                                                           revision=yr.revision,
                                                           rule_json=json.dumps(yr.to_revision_dict()),
                                                           user_id=current_user.id,
                                                           yara_rule_id=yr.id,
                                                           state=yr.state))

                return_artifacts.append(yr)
                fields_to_add[yr] = fta
        except Exception as e:
            app.logger.exception(e)
            if type(e) == UnicodeEncodeError:
                error_artifacts.append((artifact, "Unicode error: %s" % e.reason))
            else:
                error_artifacts.append((artifact, str(e)))
            app.logger.error("Failed to commit artifacts '%s'" % artifact)

    db.session.commit()

    if fields_to_add:
        for yr, fields in fields_to_add.items():
            for field in fields:
                field.artifact_id = yr.id
                field.created_user_id = current_user.id
                db.session.add(field)
        db.session.commit()

    if metadata_to_save_ip:
        metadata_cache = Metadata.get_metadata_cache()
        for metadata_to_save in metadata_to_save_ip:
            artifact, metadata = metadata_to_save
            for m in c2ip.C2ip.get_metadata_to_save(artifact, metadata, metadata_cache):
                db.session.add(m)
        db.session.commit()

    if metadata_to_save_dns:
        metadata_cache = Metadata.get_metadata_cache()
        for metadata_to_save in metadata_to_save_dns:
            artifact, metadata = metadata_to_save
            for m in c2dns.C2dns.get_metadata_to_save(artifact, metadata, metadata_cache):
                db.session.add(m)
        db.session.commit()

    return {"committed": [artifact.to_dict() for artifact in return_artifacts],
            "duplicates": duplicate_artifacts,
            "errors": error_artifacts}


#####################################################################

@app.route('/ThreatKB/import', methods=['POST'])
@auto.doc()
@login_required
def import_artifacts():
    """Import data into ThreatKB as a 2-step process. The first is extraction and the second is committing. These phases can be completed by one single call to this endpoints or by calling this endpoint for extraction and /ThreatKB/import/commit for committing.
    From Data: import_text (str),
    Optional Arguments: autocommit (int), shared_state (str), shared_reference (str), shared_description(str), shared_owner (int)
    Return: list of artifact dictionaries [{"type":"IP": "artifact": {}}, {"type":"DNS": "artifact": {}}, ...]"""
    autocommit = request.json.get("autocommit", 0)
    import_text = request.json.get('import_text', None)
    shared_state = request.json.get('shared_state', None)
    shared_reference = request.json.get("shared_reference", None)
    shared_description = request.json.get("shared_description", None)
    shared_owner = request.json.get("shared_owner", None)
    extract_ip = request.json.get('extract_ip', True)
    extract_dns = request.json.get('extract_dns', True)
    extract_signature = request.json.get('extract_signature', True)
    metadata_field_mapping = request.json.get('metadata_field_mapping', {})

    if not shared_owner:
        shared_owner = int(current_user.id)

    if not import_text:
        abort(404)

    artifacts = extract_artifacts(do_extract_ip=extract_ip, do_extract_dns=extract_dns,
                                  do_extract_signature=extract_signature, text=import_text)

    if autocommit:
        artifacts = save_artifacts(extract_ip=extract_ip, extract_dns=extract_dns, extract_signature=extract_signature,
                                   artifacts=artifacts, shared_reference=shared_reference,
                                   shared_description=shared_description, shared_state=shared_state,
                                   shared_owner=shared_owner, metadata_field_mapping=metadata_field_mapping)

    return jsonify({"artifacts": artifacts})


#####################################################################

@app.route('/ThreatKB/import_by_file', methods=['POST'])
@auto.doc()
@login_required
def import_artifacts_by_filek():
    """Import data into ThreatKB as a 2-step process. The first is extraction and the second is committing. These phases can be completed by one single call to this endpoints or by calling this endpoint for extraction and /ThreatKB/import/commit for committing.
    From Data: import_text (str),
    Optional Arguments: autocommit (int), shared_state (str), shared_reference (str), shared_description(str), shared_owner (int)
    Return: list of artifact dictionaries [{"type":"IP": "artifact": {}}, {"type":"DNS": "artifact": {}}, ...]"""
    autocommit = distutils.util.strtobool(request.values.get("autocommit", 0))
    import_text = request.files['file'].stream.read()
    import_text = import_text.strip()
    shared_state = request.values.get('shared_state', None)
    shared_reference = request.values.get("shared_reference", None) or None
    shared_description = request.values.get("shared_description", None) or None
    shared_owner = request.values.get("shared_owner", None) or None
    extract_ip = distutils.util.strtobool(request.values.get('extract_ip', True))
    extract_dns = distutils.util.strtobool(request.values.get('extract_dns', True))
    extract_signature = distutils.util.strtobool(request.values.get('extract_signature', True))
    metadata_field_mapping = request.values.get('metadata_field_mapping', {})

    if not shared_owner:
        shared_owner = int(current_user.id)

    if not import_text:
        abort(404)

    artifacts = extract_artifacts(do_extract_ip=extract_ip, do_extract_dns=extract_dns,
                                  do_extract_signature=extract_signature, text=import_text)

    if autocommit:
        artifacts = save_artifacts(extract_ip=extract_ip, extract_dns=extract_dns, extract_signature=extract_signature,
                                   artifacts=artifacts, shared_reference=shared_reference,
                                   shared_description=shared_description, shared_state=shared_state,
                                   shared_owner=shared_owner, metadata_field_mapping=metadata_field_mapping)

    return jsonify({"artifacts": artifacts})


#####################################################################

@app.route('/ThreatKB/import/commit', methods=['POST'])
@login_required
def commit_artifacts():
    """Commit previously extracted artifacts. The artifact dictionary
    From Data: artifacts (list of dicts)
    Optional Arguments: shared_reference (str), shared_description(str), shared_state (str)
    Return: dictionary of committed and duplicate artifacts {"committed": [{"type":"IP": "artifact": {}}, {"type":"DNS": "artifact": {}, ...], "duplicates": [{"type":"IP": "artifact": {}}, ...]}"""
    artifacts = request.json.get("artifacts", None)
    shared_reference = request.json.get("shared_reference", None)
    shared_description = request.json.get("shared_description", None)
    shared_state = request.json.get('shared_state', None)
    extract_ip = request.json.get('extract_ip', True)
    extract_dns = request.json.get('extract_dns', True)
    shared_owner = request.json.get("shared_owner", None)
    extract_signature = request.json.get('extract_signature', True)
    metadata_field_mapping = request.json.get('metadata_field_mapping', {})

    if not artifacts:
        abort(404)

    if not shared_owner:
        shared_owner = int(current_user.id)

    artifacts = save_artifacts(extract_ip=extract_ip, extract_dns=extract_dns, extract_signature=extract_signature,
                               artifacts=artifacts, shared_reference=shared_reference,
                               shared_description=shared_description, shared_state=shared_state,
                               metadata_field_mapping=metadata_field_mapping, shared_owner=shared_owner)
    return jsonify({"artifacts": artifacts}), 201
