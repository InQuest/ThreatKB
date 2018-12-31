import time
import datetime
import os

from app import app, db
from app.models.access_keys import AccessKeys
from flask import request, jsonify, json, abort, Response, send_file
from flask_login import current_user, login_required

from app.models.users import KBUser
from sqlalchemy import and_

"""
Token and Secret key may be passed as GET params to any API requests

i.e. /ThreatKB/access_keys?token=<token>&secret_key=<secret_key>
"""


@app.route('/ThreatKB/access_keys', methods=['GET'])
@login_required
def get_all_user_access_keys():
    """Return all user access keys
    Return: list of user access keys dictionaries"""
    keys = []
    if not current_user:
        abort(403)
    else:
        keys = AccessKeys.query.filter(AccessKeys.user_id == current_user.id).filter(AccessKeys.deleted == None).all()

    return Response(json.dumps([key.to_dict() for key in keys]), mimetype='application/json')


@app.route('/ThreatKB/access_keys/count', methods=['GET'])
@login_required
def get_active_inactive_key_count():
    """Return user's total count between active and inactive access keys
    Return: activeInactiveCount in json dictionary"""
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
    """Return access key associated with given key_id
    Return: access key dictionary"""
    key = AccessKeys.query.get(key_id)
    if not key:
        abort(404)
    if not key.user_id == current_user.id:
        abort(403)
    return jsonify(key.to_dict())


@app.route('/ThreatKB/access_keys', methods=['POST'])
@login_required
def create_access_key():
    """Create new access key if user has less than two active/inactive access keys.
    Secret key is generated, token is serialized with secret key and contains id of current user.
    Secret key (s_key) is included in return dictionary.
    Return: access key dictionary"""
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
    """Is given token Active
    Return: True if token active, False otherwise"""
    key = db.session.query(AccessKeys).join(KBUser, AccessKeys.user_id == KBUser.id).filter(
        and_(AccessKeys.token == token, KBUser.active > 0)).first()
    if not key:
        abort(403)

    if key.status == 'active':
        return True
    else:
        return False


@app.route('/ThreatKB/access_keys/<int:key_id>', methods=['PUT'])
@login_required
def update_key(key_id):
    """Update access key associated with given id.
    Only the status of a key can be updated. Able to toggle between Active/Inactive.
    Able to soft delete, but can't make active/inactive after status is Deleted.
    From Data: status(str)
    Return: access key dictionary"""
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


@app.route('/ThreatKB/access_keys/cli', methods=['GET'])
@login_required
def get_cli():
    """Download the cli script
     Return: cli file"""
    return send_file(os.path.join(os.getcwd(), "threatkb_cli.py"))
