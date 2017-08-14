from app import app, db
from app.models import tags_mapping
from flask import abort, jsonify, request
from flask.ext.login import login_required
import json

from app.routes import tags
from app.routes.tags import create_tag


@app.route('/InquestKB/tags_mapping', methods=['GET'])
@login_required
def get_all_tags_mapping():
    entities = tags_mapping.Tags_mapping.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/tags_mapping/<int:id>', methods=['GET'])
@login_required
def get_tags_mapping(id):
    entity = tags_mapping.Tags_mapping.query.get(id)
    if not entity:
        abort(404)
    return jsonify(entity.to_dict())


@app.route('/InquestKB/tags_mapping/<string:source_table>/<int:source_id>', methods=['GET'])
@login_required
def get_tags_for_source(source_table, source_id):
    entities = tags_mapping.Tags_mapping.query.filter_by(source_table=source_table, source_id=source_id).all()

    list_of_tags = []
    if not entities:
        return list_of_tags
    else:
        for entity in entities:
            entity = tags.get_tags(entity.to_dict()['tag_id'])
            if entity.status_code == 200:
                list_of_tags.append(json.loads(entity.data))

    return list_of_tags


@app.route('/InquestKB/tags_mapping', methods=['POST'])
@login_required
def create_tags_mapping_rest():
    create_tags_mapping(request.json['source'], request.json['source_id'], request.json['tags'])

    return '', 201


def create_tags_mapping(table, s_id, list_of_tags):
    for tag in list_of_tags:
        if 'id' in tag:
            t_id = tag['id']
        else:
            created_tag = create_tag(tag['text'])
            t_id = created_tag.id
            tag['id'] = t_id

        entity = tags_mapping.Tags_mapping(
            source_table=table,
            source_id=s_id,
            tag_id=t_id
        )
        db.session.add(entity)
        db.session.commit()
    return list_of_tags


def delete_tags_mapping(table, s_id, deleted_tags):
    for tag in deleted_tags:
        if 'id' in tag:
            t_id = tag['id']

            entity = tags_mapping.Tags_mapping.query.filter_by(
                source_table=table,
                source_id=s_id,
                tag_id=t_id
            ).first()
            db.session.delete(entity)
            db.session.commit()
    return


@app.route('/InquestKB/tags_mapping/<int:id>', methods=['DELETE'])
@login_required
def delete_tags_mapping_by_id(id):
    entity = tags_mapping.Tags_mapping.query.get(id)
    if not entity:
        abort(404)
    db.session.delete(entity)
    db.session.commit()
    return '', 204
