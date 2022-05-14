from flask import abort, jsonify, request, send_file, json, Response
from flask_login import login_required, current_user
from app import app, db, admin_only, auto
from app.models import scripts
import re


@app.route('/ThreatKB/scripts', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_all_scripts():
    """Return all scripts in ThreatKB
    Return: list of script dictionaries"""
    entities = scripts.Scripts.query.filter_by().all()
    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype="application/json")


@app.route('/ThreatKB/scripts/run/<int:script_id>', methods=['POST'])
@auto.doc()
@login_required
def run_script(script_id):
    """Run script and return output
    Return: dictionary of results"""

    arguments = request.json.get("arguments", None)
    arguments = re.split("[\\s\\t]", arguments)
    highlight_lines_matching = request.json.get("highlight_lines_matching", None)
    script = scripts.Scripts.query.get(script_id)
    if not script:
        abort(404)

    return Response(json.dumps(script.run_script(arguments, highlight_lines_matching)), mimetype="application/json")


@app.route('/ThreatKB/scripts/<int:script_id>', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_script_by_id(script_id):
    """Return script associated with script_id
    Return: script dictionary"""
    entity = scripts.Scripts.query.get(script_id)

    if not entity:
        abort(404)

    return Response(json.dumps(entity.to_dict()), mimetype="application/json")


@app.route('/ThreatKB/scripts/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
@admin_only()
def update_script(id):
    """Update script associated with given id
    Return: script dictionary"""
    entity = scripts.Scripts.query.get(id)
    if not entity:
        abort(404)

    entity = scripts.Scripts(
        name=request.json["name"],
        description=request.json.get("description", None),
        interpreter=request.json.get("interpreter", None),
        code=request.json.get("code", None),
        match_regex=request.json.get("match_regex", None),
        created_user_id=current_user.id,
        id=id
    )
    db.session.merge(entity)
    db.session.commit()

    script = scripts.Scripts.query.get(entity.id)
    return jsonify(script.to_dict()), 200


@app.route('/ThreatKB/scripts', methods=['POST', 'PUT'])
@auto.doc()
@login_required
@admin_only()
def create_script():
    """Create new script
    From Data: name (str), description (str), code (str), match_regex (str)
    Return: script dictionary"""
    script = scripts.Scripts(
        name=request.json["name"],
        description=request.json.get("description", None),
        code=request.json.get("code", None),
        interpreter=request.json.get("interpreter", None),
        match_regex=request.json.get("match_regex", None),
        created_user_id=current_user.id
    )

    script.created_user = current_user
    db.session.merge(script)
    db.session.commit()

    script = scripts.Scripts.query.filter(script.id).first()
    return jsonify(script.to_dict())


@app.route('/ThreatKB/scripts/<int:script_id>', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_script(script_id):
    """Delete script associated with script_id
    Return: None"""
    entity = scripts.Scripts.query.get(script_id)
    if not entity:
        abort(404)

    db.session.delete(entity)
    db.session.commit()
    return jsonify(''), 204
