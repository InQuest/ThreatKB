from app import app, db, bcrypt
from app.models.users import KBUser
from flask import request, jsonify, session, json, abort
from flask.ext.login import current_user, login_required
import flask_login


@app.route('/ThreatKB/login', methods=['POST'])
def login():
    app.logger.info("login called with payload: '%s'" % request.data)
    json_data = request.json
    user = KBUser.query.filter_by(email=json_data.get('email', None), active=True).first()
    app.logger.info("user is '%s'" % user)
    if user and bcrypt.check_password_hash(user.password, json_data['password']):
        session['logged_in'] = True
        status = True
        flask_login.login_user(user)
    else:
        status = False
    return jsonify({'result': status})


@app.route('/ThreatKB/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flask_login.logout_user()
    return jsonify({'result': 'success'})


@app.route('/ThreatKB/users', methods=['GET'])
@login_required
def get_all_users():
    users = KBUser.query.all()
    return json.dumps([user.to_dict() for user in users])


@login_required
@app.route('/ThreatKB/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = KBUser.query.get(user_id)
    if not user:
        abort(404)
    return jsonify(user.to_dict())


@app.route('/ThreatKB/users', methods=['POST'])
@login_required
def create_user():
    user = KBUser(
        email=request.json['email'],
        admin=request.json['admin'],
        password=bcrypt.generate_password_hash(request.json['password']),
        active=request.json['active']
    )

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@app.route('/ThreatKB/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    user = KBUser.query.get(user_id)
    if not user:
        abort(404)

    user = KBUser(
        email=request.json['email'],
        password=bcrypt.generate_password_hash(request.json['password'])
        if 'password' in request.json else user.password,
        admin=request.json['admin'],
        active=request.json['active'],
        id=user.id
    )

    db.session.merge(user)
    db.session.commit()

    user = KBUser.query.get(user_id)

    return jsonify(user.to_dict()), 200


@app.route('/ThreatKB/status')
def status():
    app.logger.debug("status current_user is '%s'" % (str(current_user)))
    if session.get('logged_in'):
        if session['logged_in']:
            return jsonify({'status': True})
    else:
        return jsonify({'status': False})
