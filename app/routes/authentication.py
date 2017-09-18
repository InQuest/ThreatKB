from app import app, db, bcrypt, admin_only, auto
from app.models.users import KBUser
from app.models import yara_rule, c2dns, c2ip
from flask import request, jsonify, session, json, abort
from flask.ext.login import current_user, login_required
import flask_login


@app.route('/ThreatKB/login', methods=['POST'])
@auto.doc()
def login():
    """Log a user into ThreatKB.
    Return: user dictionary"""
    app.logger.info("login called with payload: '%s'" % request.data)
    json_data = request.json
    user = KBUser.query.filter_by(email=json_data.get('email', None), active=True).first()
    app.logger.info("user is '%s'" % user)
    if user and bcrypt.check_password_hash(user.password, json_data['password']):
        session['logged_in'] = True
        s = True
        flask_login.login_user(user)
        is_admin = user.admin
    else:
        s = False
        is_admin = False
    return jsonify({'result': s, 'a': is_admin, 'user': user.to_dict()})


@app.route('/ThreatKB/logout')
@auto.doc()
@login_required
def logout():
    """Log a user out of ThreatKB.
    Return: result dictionary"""
    session.pop('logged_in', None)
    flask_login.logout_user()
    return jsonify({'result': 'success'})


@app.route('/ThreatKB/users', methods=['GET'])
@auto.doc()
@login_required
def get_all_users():
    """Return all users.
    Optional Arguments: include_inactive
    Return: list of user dictionaries"""
    include_inactive = request.args.get("include_inactive", False)

    if not include_inactive:
        users = KBUser.query.filter(KBUser.active > 0).all()
    else:
        users = KBUser.query.all()

    users = [user.to_dict() for user in users]
    users.append({"email": "Clear Owner"})
    return json.dumps(users)


@app.route('/ThreatKB/users/<int:user_id>', methods=['GET'])
@auto.doc()
@login_required
@admin_only()
def get_user(user_id):
    """Return the user associated with the given user id.
    Return: user dictionary"""
    user = KBUser.query.get(user_id)
    if not user:
        abort(404)
    return jsonify(user.to_dict())


@app.route('/ThreatKB/users', methods=['POST'])
@auto.doc()
@login_required
@admin_only()
def create_user():
    """Create a user.
    From Data: email (str), admin (bool), password (str), active (bool)
    Return: user dictionary"""
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
@auto.doc()
@login_required
@admin_only()
def update_user(user_id):
    """Update the user associated with the given user_id
    From Data: email (str), admin (bool), password (str), active (bool)
    Return: user dictionary"""
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

    if not user.active:
        yara_rule.Yara_rule.query.filter(yara_rule.Yara_rule.owner_user_id == user_id).update(dict(owner_user_id=None))
        c2dns.C2dns.query.filter(c2dns.C2dns.owner_user_id == user_id).update(dict(owner_user_id=None))
        c2ip.C2ip.query.filter(c2ip.C2ip.owner_user_id == user_id).update(dict(owner_user_id=None))

    db.session.merge(user)
    db.session.commit()
    user = KBUser.query.get(user_id)

    return jsonify(user.to_dict()), 200


@app.route('/ThreatKB/status')
@auto.doc()
def status():
    """Get the login status of the current user session.
    Return: status dictionary"""
    app.logger.debug("status current_user is '%s'" % (str(current_user)))
    if session.get('logged_in'):
        if session['logged_in']:
            return jsonify({'status': True, 'a': current_user.admin, 'user': current_user.to_dict()})
    else:
        return jsonify({'status': False, 'a': False, 'user': None})
