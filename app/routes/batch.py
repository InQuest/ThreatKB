from flask import abort, jsonify
from flask_login import current_user

from app.routes.cfg_category_range_mapping import update_cfg_category_range_mapping_current
from app.models.cfg_category_range_mapping import CfgCategoryRangeMapping
from app.models.cfg_states import verify_state
from app.routes.bookmarks import batch_delete_bookmarks
from app.routes.tags_mapping import batch_create_tags_mapping, batch_delete_tags_mapping


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


def batch_update(batch, artifact, session, include_tags=True):
    category = dict()
    fields_to_update = dict()
    if 'description' in batch and batch['description']:
        fields_to_update['description'] = batch['description']
    if 'match_type' in batch and batch['match_type']:
        fields_to_update['match_type'] = batch['match_type']
    if 'expiration_timestamp' in batch and batch['expiration_timestamp'] and hasattr(artifact, 'expiration_timestamp'):
        fields_to_update['expiration_timestamp'] = batch['expiration_timestamp']
    if 'category' in batch and batch['category'] and hasattr(artifact, 'category'):
        fields_to_update['category'] = batch['category']['category'] \
            if batch['category'] and 'category' in batch['category'] \
            else None
        category_entity = CfgCategoryRangeMapping.query \
            .filter(CfgCategoryRangeMapping.category == fields_to_update['category']) \
            .first()
        category['id'] = category_entity.id
        if category_entity and not category_entity.current:
            category['current'] = category_entity.range_min
        else:
            category['current'] = category_entity.current

        if category_entity.current + 1 > category_entity.range_max:
            abort(400)
    if 'state' in batch and batch['state']:
        fields_to_update['state'] = verify_state(batch['state']['state']) \
            if batch['state'] and 'state' in batch['state'] \
            else verify_state(batch['state'])
    if 'owner_user' in batch and batch['owner_user']:
        fields_to_update['owner_user_id'] = batch['owner_user']['id'] \
            if batch.get("owner_user", None) and batch["owner_user"].get("id", None) \
            else None

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

    return jsonify(''), 200
