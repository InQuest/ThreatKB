from sqlalchemy import bindparam

from app import app, db, admin_only, auto
from app.models import tags_mapping
from flask import abort, jsonify, request, Response
from flask_login import login_required
import json

from app.routes.tags import create_tag, get_tags


@app.route('/ThreatKB/tags_mapping', methods=['GET'])
@auto.doc()
@login_required
def get_all_tags_mapping():
    """Return all tag mappings
    Return: list of tag mapping dictionaries"""
    entities = tags_mapping.Tags_mapping.query.all()
    return Response(json.dumps([entity.to_dict() for entity in entities]), mimetype='application/json')


@app.route('/ThreatKB/tags_mapping/<int:id>', methods=['GET'])
@auto.doc()
@login_required
def get_tags_mapping(id):
    """Return tag mapping associated with the given id
    Return: tag mapping dictionary"""
    entity = tags_mapping.Tags_mapping.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/ThreatKB/tags_mapping/<string:source_table>/<int:source_id>', methods=['GET'])
@auto.doc()
@login_required
def get_tags_for_source_auth(source_table, source_id):
    """Return tag mapping associated with the given source_table and source_id
    Return: list of entity dictionaries associated with the tag"""
    return get_tags_for_source(source_table, source_id)


def get_tags_for_source(source_table, source_id):
    entities = tags_mapping.Tags_mapping.query.filter_by(source_table=source_table, source_id=source_id).all()

    list_of_tags = []
    if not entities:
        return list_of_tags
    else:
        for entity in entities:
            try:
                entity = get_tags(entity.to_dict()['tag_id'])
            except:
                continue

            if entity.status_code == 200:
                list_of_tags.append(json.loads(entity.data))

    return list_of_tags


@app.route('/ThreatKB/tags_mapping', methods=['POST', 'PUT'])
@auto.doc()
@login_required
def create_tags_mapping_rest():
    create_tags_mapping(request.json['source'], request.json['source_id'], request.json['tags'])

    return jsonify(''), 201


def batch_create_tags_mapping(table, list_of_source_ids, list_of_tags):
    tags_mapping_to_create = []
    for tag in list_of_tags:
        if 'id' in tag:
            t_id = tag['id']
        else:
            created_tag = create_tag(tag['text'])
            t_id = created_tag.id
            tag['id'] = t_id

        for s_id in list_of_source_ids:
            entity = tags_mapping.Tags_mapping.query.filter_by(
                source_table=table,
                source_id=s_id,
                tag_id=t_id
            ).first()
            if not entity:
                tags_mapping_to_create.append({
                    "source_table": table,
                    "source_id": s_id,
                    "tag_id": t_id
                })

    if tags_mapping_to_create:
        db.session.execute(tags_mapping.Tags_mapping.__table__.insert().values(
            source_table=bindparam("source_table"),
            source_id=bindparam("source_id"),
            tag_id=bindparam("tag_id")
        ), tags_mapping_to_create)
        db.session.commit()

    return list_of_tags


def create_tags_mapping(table, s_id, list_of_tags):
    tags_mapping_to_create = []
    for tag in list_of_tags:
        if 'id' in tag:
            t_id = tag['id']
        else:
            created_tag = create_tag(tag['text']) if type(tag) is dict else create_tag(tag)
            t_id = created_tag.id

        entity = tags_mapping.Tags_mapping.query.filter_by(
            source_table=table,
            source_id=s_id,
            tag_id=t_id
        ).first()
        if not entity:
            tags_mapping_to_create.append({
                "source_table": table,
                "source_id": s_id,
                "tag_id": t_id
            })

    if tags_mapping_to_create:
        db.session.execute(tags_mapping.Tags_mapping.__table__.insert().values(
            source_table=bindparam("source_table"),
            source_id=bindparam("source_id"),
            tag_id=bindparam("tag_id")
        ), tags_mapping_to_create)
        db.session.commit()

    return list_of_tags


def delete_tags_mapping(table, s_id):
    tags_mapping.Tags_mapping.query.filter_by(
        source_table=table,
        source_id=s_id
    ).delete()
    db.session.commit()
    return


def batch_delete_tags_mapping(table, list_of_source_ids):
    db.session.execute(tags_mapping.Tags_mapping.__table__
                       .delete()
                       .where(tags_mapping.Tags_mapping.source_table == table
                              and tags_mapping.Tags_mapping.source_id.in_(list_of_source_ids)))
    db.session.commit()


@app.route('/ThreatKB/tags_mapping/<int:id>', methods=['DELETE'])
@login_required
@admin_only()
def delete_tags_mapping_by_id(id):
    entity = tags_mapping.Tags_mapping.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return jsonify(''), 204
