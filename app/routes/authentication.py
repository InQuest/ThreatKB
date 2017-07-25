from app import app, bcrypt
from app.models.authentication import KBUser
from flask import request, jsonify, session


@app.route('/InquestKB/login', methods=['POST'])
def login():
    app.logger.info("login called with payload: '%s'" % (request.data))
    json_data = request.json
    user = KBUser.query.filter_by(email=json_data['email']).first()
    app.logger.info("user is '%s'" % (user))
    if user and bcrypt.check_password_hash(user.password, json_data['password']):
        session['logged_in'] = True
        status = True
    else:
        status = False
    return jsonify({'result': status})


@app.route('/InquestKB/logout')
def logout():
    session.pop('logged_in', None)
    return jsonify({'result': 'success'})


@app.route('/InquestKB/status')
def status():
    app.logger.info("session is: '%s'" % (session))
    if session.get('logged_in'):
        if session['logged_in']:
            return jsonify({'status': True})
    else:
        return jsonify({'status': False})
