from flask import abort, jsonify, request
from flask.ext.login import login_required, current_user
from app import app, db
from app.models import c2ip, c2dns, yara_rule, cfg_states
from app.utilities import extract_artifacts


#####################################################################

def save_artifacts(artifacts):
    state = "Imported"
    return_artifacts = []

    if not cfg_states.Cfg_states.query.filter_by(state=state).first():
        db.session.add(cfg_states.Cfg_states(state=state))
        db.session.commit()

    for artifact in artifacts:
        try:
            if artifact["type"].lower() == "ip":
                ip = c2ip.C2ip.get_c2ip_from_ip(artifact["artifact"])
                ip.created_user_id, ip.modified_user_id = current_user.id, current_user.id
                ip.state = state
                db.session.add(ip)
                return_artifacts.append(ip)
            elif artifact["type"].lower() == "dns":
                dns = c2dns.C2dns.get_c2dns_from_hostname(artifact["artifact"])
                dns.created_user_id, dns.modified_user_id = current_user.id, current_user.id
                dns.state = state
                db.session.add(dns)
                return_artifacts.append(dns)
            elif artifact["type"].lower() == "yara_rule":
                yr = yara_rule.Yara_rule.get_yara_rule_from_yara_dict(artifact["rule"])
                yr.created_user_id, yr.modified_user_id = current_user.id, current_user.id
                yr.state = state
                db.session.add(yr)
                return_artifacts.append(yr)
        except:
            pass

    db.session.commit()
    return [artifact.to_dict() for artifact in return_artifacts]


#####################################################################

@app.route('/InquestKB/import', methods=['POST'])
@login_required
def import_artifacts():
    autocommit = request.json.get("autocommit", 0)

    import_text = request.json.get('import_text', None)

    if not import_text:
        abort(404)

    artifacts = extract_artifacts(import_text)

    if autocommit:
        artifacts = save_artifacts(artifacts)

    return jsonify({"artifacts": artifacts})


#####################################################################

@app.route('/InquestKB/import/commit', methods=['POST'])
@login_required
def commit_artifacts():
    artifacts = request.json.get("artifacts", None)

    if not artifacts:
        abort(404)

    artifacts = save_artifacts(artifacts)
    return jsonify({"artifacts": artifacts}), 201
