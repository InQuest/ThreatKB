import time

import datetime

import os

from app import app, db
from app.models.access_keys import AccessKeys
from flask import request, jsonify, json, abort
from flask.ext.login import current_user, login_required

from app.models.users import KBUser


@app.route('/ThreatKB/access_keys', methods=['GET'])
@login_required
def get_all_user_access_keys():
    keys = []
    if not current_user:
        abort(403)
    else:
        keys = AccessKeys.query.filter(AccessKeys.user_id == current_user.id).all()

    return json.dumps([key.to_dict() for key in keys])


@app.route('/ThreatKB/access_keys/count', methods=['GET'])
@login_required
def get_active_inactive_key_count():
    keys = []
    if not current_user:
        abort(403)
    else:
        keys = AccessKeys.query.filter(AccessKeys.user_id == current_user.id).all()

    count = 0
    for key in keys:
        if key.status == 'active' or key.status == 'inactive':
            count += 1

    return jsonify({'activeInactiveCount': count})


@app.route('/ThreatKB/access_keys/<int:key_id>', methods=['GET'])
@login_required
def get_access_key(key_id):
    key = AccessKeys.query.get(key_id)
    if not key:
        abort(404)
    if not key.user_id == current_user.id:
        abort(403)
    return jsonify(key.to_dict())


@app.route('/ThreatKB/access_keys', methods=['POST'])
@login_required
def create_access_key():
    user = KBUser.query.get(current_user.id)
    if not user:
        abort(403)
    active_inactive_count = json.loads(get_active_inactive_key_count().data)

    if active_inactive_count and active_inactive_count['activeInactiveCount'] < 2:
        s_key = os.urandom(24).encode('hex')
        token = user.generate_auth_token(s_key)

        key = AccessKeys(
            user_id=current_user.id,
            token=token
        )

        db.session.add(key)
        db.session.commit()

        gen_key = key.to_dict()
        gen_key['s_key'] = s_key

        return jsonify(gen_key), 201
    else:
        return abort(403)


def is_token_active(token):
    key = AccessKeys.query.filter_by(token=token).first()
    if not key:
        abort(403)

    if key.status == 'active':
        return True
    else:
        return False


@app.route('/ThreatKB/access_keys/<int:key_id>', methods=['PUT'])
@login_required
def update_key(key_id):
    key = AccessKeys.query.get(key_id)
    if not key:
        abort(404)
    if not key.user_id == current_user.id:
        abort(403)

    key = AccessKeys(
        id=key.id,
        user_id=current_user.id,
        token=key.token,
        created=key.created,
        deleted=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        if 'status' in request.json and request.json['status'] == 'deleted' else None,
        status=request.json['status']
    )

    db.session.merge(key)
    db.session.commit()

    key = AccessKeys.query.get(key_id)

    return jsonify(key.to_dict()), 200
