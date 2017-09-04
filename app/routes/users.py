from app import app
from app.models.users import KBUser
from flask import abort
import json
from flask.ext.login import login_required

@app.route('/InquestKB/users', methods=['GET'])
@login_required
def get_all_users():
    entities = KBUser.query.all()
    return json.dumps([entity.to_dict() for entity in entities])


@app.route('/InquestKB/users/<int:id>', methods=['GET'])
@login_required
def get_user(id):
    entity = KBUser.query.get(id)
    if not entity:
        abort(404)
    return json.dumps(entity.to_dict()), 200
