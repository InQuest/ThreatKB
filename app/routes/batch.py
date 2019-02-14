from flask import abort, jsonify
from flask_login import current_user

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
    for b in batch['ids']:
        entity = artifact.query.get(b)
        if not entity:
            abort(404)
        if not current_user.admin and entity.owner_user_id != current_user.id:
            abort(403)

    fields_to_update = dict()
    if 'state' in batch and batch['state']:
        fields_to_update['state'] = verify_state(batch['state']['state']) \
            if batch['state'] and 'state' in batch['state'] \
            else verify_state(batch['state'])
    if 'owner_user' in batch and batch['owner_user']:
        fields_to_update['owner_user_id'] = batch['owner_user']['id'] \
            if batch.get("owner_user", None) and batch["owner_user"].get("id", None) \
            else None

    if fields_to_update and 'ids' in batch and batch['ids']:
        session.execute(artifact.__table__.update().values(
            fields_to_update
        ).where(artifact.id.in_(batch['ids'])))
        session.commit()

    if include_tags and 'tags' in batch and batch['tags']:
        batch_create_tags_mapping(artifact.__tablename__, batch['ids'], batch['tags'])

    return jsonify(''), 200
