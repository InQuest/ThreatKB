from app import app, db, admin_only, auto
from app.models import cfg_category_range_mapping
from flask import abort, jsonify, request
from flask.ext.login import login_required
import json


@app.route('/ThreatKB/cfg_category_range_mapping', methods=['GET'])
@auto.doc()
@login_required
def get_all_cfg_category_range_mappings():
    """Return list of all category range mappings
    Return: list of category range mapping dictionaries"""
    entities = cfg_category_range_mapping.CfgCategoryRangeMapping.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/ThreatKB/cfg_category_range_mapping/<int:id>', methods=['GET'])
@login_required
@admin_only()
def get_cfg_category_range_mapping(id):
    """Return category range mapping associated with the given id
    Return: category range mapping dictionary"""
    entity = cfg_category_range_mapping.CfgCategoryRangeMapping.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/cfg_category_range_mapping', methods=['POST'])
@auto.doc()
@login_required
@admin_only()
def create_cfg_category_range_mapping():
    """Create category range mapping
    Retun: category range mapping dictionary"""
    entity = cfg_category_range_mapping.CfgCategoryRangeMapping(
        category=request.json['category'],
        range_min=request.json['range_min'],
        range_max=request.json['range_max']
    )
    db.session.add(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 201


@app.route('/ThreatKB/cfg_category_range_mapping/<int:id>', methods=['PUT'])
@auto.doc()
@login_required
@admin_only()
def update_cfg_category_range_mapping(id):
    """Update category range mapping associated with the given id
    From Data: category (str), range_min (int), range_max (int)
    Return: category range mapping dictionary"""
    entity = cfg_category_range_mapping.CfgCategoryRangeMapping.query.get(id)
    if not entity:
        abort(404)
    entity = cfg_category_range_mapping.CfgCategoryRangeMapping(
        category=request.json['category'],
        range_min=request.json['range_min'],
        range_max=request.json['range_max'],
        id=id
    )
    db.session.merge(entity)
    db.session.commit()
    return jsonify(entity.to_dict()), 200


def update_cfg_category_range_mapping_current(id, current):
    entity = cfg_category_range_mapping.CfgCategoryRangeMapping.query.get(id)
    if not entity:
        return
    entity = cfg_category_range_mapping.CfgCategoryRangeMapping(
        category=entity.category,
        range_min=entity.range_min,
        range_max=entity.range_max,
        current=current,
        id=id
    )
    db.session.merge(entity)
    db.session.commit()
    return


@app.route('/ThreatKB/cfg_category_range_mapping/<int:id>', methods=['DELETE'])
@auto.doc()
@login_required
@admin_only()
def delete_cfg_category_range_mapping(id):
    """Delete category range mapping associated with the given id
    Return: None"""
    entity = cfg_category_range_mapping.CfgCategoryRangeMapping.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
