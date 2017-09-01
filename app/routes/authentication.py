from app import app, bcrypt
from app.models.authentication import KBUser
from flask import request, jsonify, session
from flask.ext.login import current_user, login_required
import flask_login


@app.route('/ThreatKB/login', methods=['POST'])
def login():
    app.logger.info("login called with payload: '%s'" % (request.data))
    json_data = request.json
    user = KBUser.query.filter_by(email=json_data.get('email', None)).first()
    app.logger.info("user is '%s'" % (user))
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


@app.route('/ThreatKB/status')
def status():
    app.logger.debug("status current_user is '%s'" % (str(current_user)))
    if session.get('logged_in'):
        if session['logged_in']:
            return jsonify({'status': True})
    else:
        return jsonify({'status': False})
