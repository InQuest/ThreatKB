from sqlalchemy import bindparam, and_

from app import app, db, admin_only, auto
from app.models import tags_mapping, tags
from flask import abort, jsonify, request, Response
from flask_login import login_required, current_user
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


@app.route('/ThreatKB/tags_mapping', methods=['POST'])
@auto.doc()
@login_required
def create_tags_mapping_rest():
    merge_tags_mapping(request.json['source'], request.json['source_id'], request.json['tags'])

    return jsonify(''), 201


def batch_create_tags_mapping(table, list_of_source_ids, list_of_tags, no_delete=True):
    for entity_id in list_of_source_ids:
        merge_tags_mapping(table, entity_id, list_of_tags, no_delete)

    return list_of_tags


def merge_tags_mapping(table_name, entity_id, entity_tags, no_delete=False):
    current_tags = db.session.query(tags_mapping.Tags_mapping, tags.Tags) \
        .filter(tags_mapping.Tags_mapping.source_table == table_name) \
        .filter(tags_mapping.Tags_mapping.source_id == entity_id) \
        .filter(tags_mapping.Tags_mapping.tag_id == tags.Tags.id) \
        .all()
    current_tags_text = [current_tag[1].text for current_tag in current_tags]
    removed_tags = [current_tag[1].text for current_tag in current_tags]

    for tag in entity_tags:
        try:
            tag = tag["text"]
        except TypeError, e:
            pass

        if not tag in current_tags_text:
            new_tag_mapping = tags_mapping.Tags_mapping()
            new_tag_mapping.source_id = entity_id
            new_tag_mapping.source_table = table_name
            if tag in current_tags_text:
                new_tag_mapping.tag_id = current_tags[current_tags_text.index(tag)][1].id
            else:
                new_tag = tags.Tags()
                new_tag.text = tag
                new_tag.created_user_id = current_user.id
                db.session.add(new_tag)
                db.session.flush()
                new_tag_mapping.tag_id = new_tag.id
            new_tag_mapping.created_user_id = current_user.id
            db.session.add(new_tag_mapping)
        else:
            removed_tags.remove(tag)

    if not no_delete:
        for tag in removed_tags:
            removed_tag = current_tags[current_tags_text.index(tag)][0]
            db.session.delete(removed_tag)

    db.session.commit()


def delete_tags_mapping(table, s_id):
    tags_to_delete = db.session.query(tags_mapping.Tags_mapping).filter(
        and_(tags_mapping.Tags_mapping.source_table == table, tags_mapping.Tags_mapping.source_id == s_id)).all()
    for tag in tags_to_delete:
        db.session.delete(tag)
    db.session.commit()
    return


def batch_delete_tags_mapping(table, list_of_source_ids):
    tags_to_delete = db.session.query(tags_mapping.Tags_mapping).filter(
        and_(tags_mapping.Tags_mapping.source_table == table,
             tags_mapping.Tags_mapping.source_id.in_(list_of_source_ids))).all()
    for tag in tags_to_delete:
        db.session.delete(tag)
    db.session.commit()
    return

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
