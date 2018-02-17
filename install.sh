#!/bin/bash
# Bootstrap script to setup environment for ThreatKB

virtualenv flask
if [ $? -ne 0]; then
    echo "error: failed to setup virtual environemtn!"
    exit 1
fi

flask/bin/pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "error: failed to install python requirements.txt"
    exit 1
fi

flask/bin/python manage.py db upgrade
if [ $? -ne 0 ]; then
    echo "error: failed to run 'manage.py db upgrade'"
    exit 1
fi

bower install
if [ $? -ne 0 ]; then
    echo "error: failed to install bower requirements!"
    exit 1
fi

