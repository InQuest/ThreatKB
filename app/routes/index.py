from app import app, auto
from flask import send_from_directory
import os

@app.route('/')
@auto.doc()
def root():
    """Root route
    Return: index.html"""
    return app.send_static_file('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
