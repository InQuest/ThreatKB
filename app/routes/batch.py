from flask import abort, jsonify
from flask_login import current_user

from app.routes.cfg_category_range_mapping import update_cfg_category_range_mapping_current
from app.models.metadata import Metadata, MetadataMapping
from app.models.cfg_category_range_mapping import CfgCategoryRangeMapping
from app.models.cfg_states import verify_state
from app.routes.bookmarks import batch_delete_bookmarks
from app.routes.tags_mapping import batch_create_tags_mapping, batch_delete_tags_mapping
from app.routes.comments import create_batch_comments


def batch_delete(batch, artifact, session, entity_mapping, is_yara=False):
    if 'ids' in batch and batch['ids']:
        for b in batch['ids']:
            entity = artifact.query.get(b)
            if not entity:
                abort(404)
            if not current_user.admin and entity.owner_user_id != current_user.id:
                abort(403)

        if is_yara:
            session.execute(artifact.__table__.update().values(
                {'active': False}
            ).where(artifact.id.in_(batch['ids'])))
        else:
            session.execute(artifact.__table__.delete().where(artifact.id.in_(batch['ids'])))
        session.commit()

        if not is_yara:
            batch_delete_tags_mapping(artifact.__tablename__, batch['ids'])
        batch_delete_bookmarks(entity_mapping, batch['ids'], current_user.id)

    return jsonify(''), 200


def batch_update(batch, artifact, session, entity_mapping, include_tags=True):
    category = dict()
    fields_to_update = dict()
    for key, value in batch.items():
        if value and hasattr(artifact, key):
            if key == 'category':
                fields_to_update[key] = value[key] \
                    if value and key in value \
                    else None
                category_entity = CfgCategoryRangeMapping.query \
                    .filter(CfgCategoryRangeMapping.category == fields_to_update[key]) \
                    .first()
                category['id'] = category_entity.id
                if category_entity and not category_entity.current:
                    category['current'] = category_entity.range_min
                else:
                    category['current'] = category_entity.current

                if category_entity.current + 1 > category_entity.range_max:
                    abort(400)
            elif key == 'state':
                fields_to_update[key] = verify_state(value[key]) \
                    if value and key in value \
                    else verify_state(value)
            elif key == 'owner_user':
                fields_to_update['owner_user_id'] = value['id'] \
                    if batch.get("owner_user", None) and value.get("id", None) \
                    else None
            elif key == 'mitre_techniques' or key == '_mitre_techniques':
                fields_to_update['_mitre_techniques'] = ",".join(value)
            elif key == 'mitre_tactics' or key == '_mitre_tactics':
                fields_to_update['_mitre_tactics'] = ",".join(value)
            else:
                if key not in ('comments', 'tags', 'metadata', 'metadata_values'):
                    fields_to_update[key] = value

    artifact_events_to_update = []
    for batch_id in batch['ids']:
        entity = artifact.query.get(batch_id)
        if not entity:
            abort(404)
        if not current_user.admin and entity.owner_user_id != current_user.id:
            abort(403)
        if 'category' in fields_to_update and fields_to_update['category'] and hasattr(artifact, 'eventid') and \
                entity.category != fields_to_update['category']:
            category['current'] = category['current'] + 1
            artifact_events_to_update.append({
                'event_id': category['current'],
                'artifact_id': batch_id
            })

    if fields_to_update and 'ids' in batch and batch['ids']:
        session.execute(artifact.__table__.update().values(
            fields_to_update
        ).where(artifact.id.in_(batch['ids'])))

        for artifact_events_to_update in artifact_events_to_update:
            session.execute(artifact.__table__.update().values(
                {'eventid': artifact_events_to_update['event_id']}
            ).where(artifact.id == artifact_events_to_update['artifact_id']))

        if category:
            update_cfg_category_range_mapping_current(category['id'], category['current'])
        session.commit()

    if include_tags and 'tags' in batch and batch['tags']:
        batch_create_tags_mapping(artifact.__tablename__, batch['ids'], batch['tags'])

    if 'comments' in batch and batch['comments']:
        create_batch_comments(batch['comments'],
                              entity_mapping,
                              batch['ids'],
                              current_user.id)

    if 'metadata_values' in batch and batch['metadata_values']:
        save_batch_metadata_values(session, batch['metadata_values'], entity_mapping, batch['ids'], current_user.id)

    return jsonify(''), 200


def save_batch_metadata_values(session, metadata_values, entity_mapping, batch_ids, user_id):
    dirty = False
    for name, value_dict in metadata_values.iteritems():
        if not name or not value_dict:
            continue

        for batch_id in batch_ids:
            m = session.query(MetadataMapping).join(Metadata, Metadata.id == MetadataMapping.metadata_id) \
                .filter(Metadata.key == name) \
                .filter(Metadata.artifact_type == entity_mapping) \
                .filter(MetadataMapping.artifact_id == batch_id) \
                .first()
            if m:
                m.value = value_dict["value"]
                session.add(m)
                dirty = True
            else:
                m = session.query(Metadata) \
                    .filter(Metadata.key == name) \
                    .filter(Metadata.artifact_type == entity_mapping) \
                    .first()
                session.add(MetadataMapping(value=value_dict["value"],
                                            metadata_id=m.id,
                                            artifact_id=batch_id,
                                            created_user_id=user_id))
                dirty = True
    if dirty:
        session.commit()
