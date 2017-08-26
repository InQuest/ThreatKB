from flask import abort, jsonify, request
from flask.ext.login import login_required, current_user
from app import app, db
from app.models import c2ip, c2dns, yara_rule, cfg_states, users, comments
from app.utilities import extract_artifacts


#####################################################################

def save_artifacts(artifacts, shared_reference=None, shared_state=None):
    default_state = "Imported"
    return_artifacts = []
    duplicate_artifacts = []

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

                db.session.add(yr)
                return_artifacts.append(yr)
        except Exception, e:
            app.logger.exception(e)
            app.logger.error("Failed to commit artifacts '%s'" % (artifact))

    db.session.commit()
    return {"committed": [artifact.to_dict() for artifact in return_artifacts],
            "duplicates": duplicate_artifacts}


#####################################################################

@app.route('/InquestKB/import', methods=['POST'])
@login_required
def import_artifacts():
    autocommit = request.json.get("autocommit", 0)
    import_text = request.json.get('import_text', None)
    shared_state = request.json.get('shared_state', None)
    shared_reference = request.json.get("shared_reference", None)

    if not import_text:
        abort(404)

    artifacts = extract_artifacts(import_text)

    if autocommit:
        artifacts = save_artifacts(artifacts=artifacts, shared_reference=shared_reference, shared_state=shared_state)

    return jsonify({"artifacts": artifacts})


#####################################################################

@app.route('/InquestKB/import/commit', methods=['POST'])
@login_required
def commit_artifacts():
    artifacts = request.json.get("artifacts", None)
    shared_reference = request.json.get("shared_reference", None)
    shared_state = request.json.get('shared_state', None)

    if not artifacts:
        abort(404)

    artifacts = save_artifacts(artifacts=artifacts, shared_reference=shared_reference, shared_state=shared_state)
    return jsonify({"artifacts": artifacts}), 201
