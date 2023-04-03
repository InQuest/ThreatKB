#!/usr/bin/env bash

set -x

env

cd /opt/threatkb
./wait-for-it.sh db:3306 -- echo "db is up"

if [[ ! -z "${RUN_AGENT}" ]]; then
  env/bin/celery -A app.celery worker --uid uwsgi --loglevel=info
else
  find . -name "*.pyc" -exec rm -f {} \;
  env/bin/flask db upgrade

  num_users=`echo "select count(*) from kb_users;" | mysql -u ${SQL_USERNAME} -p"${SQL_PASSWORD}" -h ${SQL_HOST} ${SQL_DATABASE} | sed 's/[^0-9]//g'`
  if [ $num_users -lt 1 ]; then
    PASSWORD=`env/bin/python3.8 hash_pass.py ${THREATKB_PASS}`
    mysql -u ${SQL_USERNAME} -p"${SQL_PASSWORD}" ${SQL_DATABASE} -h ${SQL_HOST} -e "insert into kb_users (email,password,admin,active) values (\"${THREATKB_USER}\", \"${PASSWORD}\", 1, 1);"
  fi
  #env/bin/python run.py --listen-on ${LISTEN_ON} --listen-port ${LISTEN_PORT}
  env/bin/python3.8 run.py --listen-on "${LISTEN_ON:-0.0.0.0}" --listen-port "${LISTEN_PORT:-5000}"
fi
