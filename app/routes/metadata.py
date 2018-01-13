from app import app, db, auto, admin_only, ENTITY_MAPPING
from app.models import metadata
from flask import abort, jsonify, request, Response
from flask.ext.login import login_required, current_user
from dateutil import parser
import json


@app.route('/ThreatKB/metadata', methods=['GET'])
@auto.doc()
@login_required
def get_all_metadata():
    """Return all active metadata
    Return: list of metadata dictionaries"""
    active_only = request.args.get("active_only", True)
    artifact_type = request.args.get("artifact_type", 0)
    format = request.args.get("format", "list")
    filter = request.args.get("filter", None)

    if format == "dict" and filter:
        return Response(json.dumps([metadata.Metadata.get_metadata_dict(filter.upper())]), mimetype="application/json")

    q = metadata.Metadata.query
    q = q.filter_by(active=active_only)
    if artifact_type:
        q = q.filter_by(artifact_type == artifact_type)

    if filter:
        return Response(json.dumps([entity.to_dict() for entity in q.all() if entity.to_dict()["type"] == filter]),
                        mimetype='application/json')
    else:
        return Response(json.dumps([entity.to_dict() for entity in q.all()]), mimetype='application/json')


@app.route('/ThreatKB/metadata/<int:id>', methods=['GET'])
@login_required
@auto.doc()
def get_metadata(id):
    """Return task associated with given id
    Return: task dictionary"""
    entity = metadata.Metadata.query.get(id)
    if not entity:
        abort(404)

    return jsonify(entity.to_dict())


@app.route('/ThreatKB/metadata', methods=['POST'])
@auto.doc()
@login_required
@admin_only()
def create_metadata():
    """Create new metadata
    From Data: key (str), active (int), artifact_type (int), type (str), default (str), show_in_table (int)
    Return: task dictionary"""

    type_ = request.json['type']
    default = request.json.get('default', None)
    choices = request.json.get("choices", "")
    choices = [choice.strip() for choice in choices.split(",") if len(choice) > 0]

    if type_.lower() == "integer" and default:
        default = int(default)

    if type_.lower() == "date" and default:
        default = parser.parse(default)

    if type_.lower() == "select" and not choices:
        raise Exception("You must provide choices with the select option")

    entity = metadata.Metadata(
        key=request.json['key']
        , active=request.json.get('active', 1)
        , artifact_type=request.json['artifact_type']
        , type_=type_
        , default=default
        , show_in_table=0
        , required=request.json.get("required", 0)
        , export_with_release=request.json.get("export_with_release", 1)
        , created_user_id=current_user.id
    )
    db.session.add(entity)
    db.session.commit()

    for choice in choices:
        db.session.add(metadata.MetadataChoices(choice=choice, metadata_id=entity.id, created_user_id=current_user.id))
    db.session.commit()

    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/metadata', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_metadata_by_id_in_param():
    """Delete metadata associated with the given id
    Return: None"""
    id = request.args.get("id")
    entity = metadata.Metadata.query.get(id)

    if not entity:
        abort(404)

    entity.active = False
    db.session.add(entity)
    db.session.commit()

    return jsonify(''), 204


@app.route('/ThreatKB/metadata/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_metadata(id):
    """Delete metadata associated with the given id
    Return: None"""
    entity = metadata.Metadata.query.get(id)

    if not entity:
        abort(404)

    # db.session.delete(entity)
    entity.active = False
    db.session.add(entity)
    db.session.commit()

    return jsonify(''), 204
