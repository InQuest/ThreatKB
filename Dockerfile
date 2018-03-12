FROM ubuntu:14.04

ADD . /opt/threatkb


RUN apt-get update
RUN apt-get install -y git libsqlite3-dev python2.7 python-pip npm libffi-dev libssl-dev mysql-client libmysqlclient-dev python-dev libpython-dev git
RUN pip install virtualenv
RUN npm install -g bower
RUN ln -s /usr/bin/nodejs /usr/bin/node

WORKDIR /opt/threatkb

RUN virtualenv env
RUN env/bin/pip install -r requirements.txt
RUN bower install --allow-root
RUN git log -1 --format="%H" > version
RUN git log -1 --format="%cE" >> version
RUN git log -1 --format="%ci" >> version
RUN chmod 744 docker-entrypoint.sh
RUN chmod 744 wait-for-it.sh
RUN apt-get update
RUN apt-get install -y apt-transport-https ca-certificates curl software-properties-common
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
RUN apt-key fingerprint 0EBFCD88
RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
RUN apt-get update
RUN apt-get install -y docker-ce

CMD ["/opt/threatkb/docker-entrypoint.sh"]
