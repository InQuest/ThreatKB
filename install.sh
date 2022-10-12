#!/bin/bash
# Bootstrap script to setup environment for ThreatKB

python3 -m venv env
if [ $? -ne 0 ]; then
    echo "error: failed to setup virtual environment!"
    exit 1
fi

env/bin/pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "error: failed to install python requirements.txt"
    exit 1
fi

env/bin/python3 manage.py db upgrade
if [ $? -ne 0 ]; then
    echo "error: failed to run 'python3 db upgrade'"
    exit 1
fi

bower install
if [ $? -ne 0 ]; then
    echo "error: failed to install bower requirements!"
    exit 1
fi

