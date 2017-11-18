FROM ubuntu:14.04

ADD . /opt/threatkb


RUN apt-get update
RUN apt-get install -y libsqlite3-dev python2.7 python-pip npm libffi-dev libssl-dev mysql-client libmysqlclient-dev python-dev libpython-dev git
RUN pip install virtualenv
RUN npm install -g bower
RUN ln -s /usr/bin/nodejs /usr/bin/node

WORKDIR /opt/threatkb

RUN virtualenv env
RUN env/bin/pip install -r requirements.txt
RUN bower install --allow-root
RUN chmod 744 docker-entrypoint.sh
RUN chmod 744 wait-for-it.sh

CMD ["/opt/threatkb/docker-entrypoint.sh"]
