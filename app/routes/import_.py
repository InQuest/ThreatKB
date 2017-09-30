from flask import abort, jsonify, request
from flask.ext.login import login_required, current_user
from app import app, db, admin_only, auto
from app.models import c2ip, c2dns, yara_rule, cfg_states, cfg_settings, comments
from app.utilities import extract_artifacts
import json


#####################################################################

def save_artifacts(artifacts, shared_reference=None, shared_state=None, shared_owner=None):
    default_state = "Imported"
    return_artifacts = []
    duplicate_artifacts = []

    preserve_event_id = cfg_settings.Cfg_settings.get_setting(key="PRESERVE_EVENT_ID_ON_IMPORT")
    try:
        preserve_event_id = json.loads(preserve_event_id)
    except:
        pass

    if not cfg_states.Cfg_states.query.filter_by(state=default_state).first():
        db.session.add(cfg_states.Cfg_states(state=default_state))
        db.session.commit()

    for artifact in artifacts:
        try:
            if artifact["type"].lower() == "ip":
                old_ip = c2ip.C2ip.query.filter(c2ip.C2ip.ip == artifact["artifact"]).first()
                if old_ip:
                    message = "System comment: duplicate IP '%s' found at '%s' by '%s'" % (
                    artifact["artifact"], shared_reference if shared_reference else "no reference provided",
                    current_user.email)
                    db.session.add(
                        comments.Comments(comment=message, entity_type=comments.Comments.ENTITY_MAPPING["IP"],
                                          entity_id=old_ip.id, user_id=current_user.id))
                    duplicate_artifacts.append(artifact)
                else:
                    ip = c2ip.C2ip.get_c2ip_from_ip(artifact["artifact"])
                    ip.created_user_id, ip.modified_user_id = current_user.id, current_user.id
                    ip.state = default_state if not shared_state else shared_state
                    if shared_reference:
                        ip.reference_link = shared_reference

                    if shared_owner:
                        ip.owner_user_id = shared_owner

                    db.session.add(ip)
                    return_artifacts.append(ip)
            elif artifact["type"].lower() == "dns":
                old_dns = c2dns.C2dns.query.filter(c2dns.C2dns.domain_name == artifact["artifact"]).first()
                if old_dns:
                    message = "System comment: duplicate DNS '%s' found at '%s' by '%s'" % (
                    artifact["artifact"], shared_reference if shared_reference else "no reference provided",
                    current_user.email)
                    db.session.add(
                        comments.Comments(comment=message, entity_type=comments.Comments.ENTITY_MAPPING["DNS"],
                                          entity_id=old_dns.id, user_id=current_user.id))
                    duplicate_artifacts.append(artifact)
                else:
                    dns = c2dns.C2dns.get_c2dns_from_hostname(artifact["artifact"])
                    dns.created_user_id, dns.modified_user_id = current_user.id, current_user.id
                    dns.state = default_state if not shared_state else shared_state
                    if shared_reference:
                        dns.reference_link = shared_reference
                    if shared_state:
                        dns.state = shared_state
                    if shared_owner:
                        dns.owner_user_id = shared_owner


                    db.session.add(dns)
                    return_artifacts.append(dns)
            elif artifact["type"].lower() == "yara_rule":
                yr = yara_rule.Yara_rule.get_yara_rule_from_yara_dict(artifact["rule"])
                yr.created_user_id, yr.modified_user_id = current_user.id, current_user.id
                yr.state = default_state if not shared_state else shared_state
                if shared_reference:
                    yr.reference_link = shared_reference
                if shared_state:
                    yr.state = shared_state
                if shared_owner:
                    yr.owner_user_id = shared_owner
                if not preserve_event_id:
                    yr.eventid = None

                db.session.add(yr)
                return_artifacts.append(yr)
        except Exception, e:
            app.logger.exception(e)
            app.logger.error("Failed to commit artifacts '%s'" % (artifact))

    db.session.commit()
    return {"committed": [artifact.to_dict() for artifact in return_artifacts],
            "duplicates": duplicate_artifacts}


#####################################################################

@app.route('/ThreatKB/import', methods=['POST'])
@auto.doc()
@login_required
@admin_only()
def import_artifacts():
    """Import data into ThreatKB as a 2-step process. The first is extraction and the second is committing. These phases can be completed by one single call to this endpoints or by calling this endpoint for extraction and /ThreatKB/import/commit for committing.
    From Data: import_text (str),
    Optional Arguments: autocommit (int), shared_state (str), shared_reference (str), shared_owner (int)
    Return: list of artifact dictionaries [{"type":"IP": "artifact": {}}, {"type":"DNS": "artifact": {}}, ...]"""
    autocommit = request.json.get("autocommit", 0)
    import_text = request.json.get('import_text', None)
    shared_state = request.json.get('shared_state', None)
    shared_reference = request.json.get("shared_reference", None)
    shared_owner = request.json.get("shared_owner", None)

    if shared_owner:
        shared_owner = int(shared_owner)

    if not import_text:
        abort(404)

    artifacts = extract_artifacts(import_text)

    if autocommit:
        artifacts = save_artifacts(artifacts=artifacts, shared_reference=shared_reference, shared_state=shared_state,
                                   shared_owner=shared_owner)

    return jsonify({"artifacts": artifacts})


#####################################################################

@app.route('/ThreatKB/import/commit', methods=['POST'])
@login_required
@admin_only()
def commit_artifacts():
    """Commit previously extracted artifacts. The artifact dictionary
    From Data: artifacts (list of dicts)
    Optional Arguments: shared_reference (str), shared_state (str)
    Return: dictionary of committed and duplicate artifacts {"committed": [{"type":"IP": "artifact": {}}, {"type":"DNS": "artifact": {}, ...], "duplicates": [{"type":"IP": "artifact": {}}, ...]}"""
    artifacts = request.json.get("artifacts", None)
    shared_reference = request.json.get("shared_reference", None)
    shared_state = request.json.get('shared_state', None)

    if not artifacts:
        abort(404)

    artifacts = save_artifacts(artifacts=artifacts, shared_reference=shared_reference, shared_state=shared_state)
    return jsonify({"artifacts": artifacts}), 201
