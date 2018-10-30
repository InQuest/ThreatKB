FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y git libsqlite3-dev python2.7 python-pip npm libffi-dev libssl-dev mysql-client \
    libmysqlclient-dev python-dev libpython-dev git yara=3.4.0+dfsg-2build1 apt-transport-https ca-certificates curl \
    software-properties-common libpcre3 libpcre3-dev

RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - \
    && apt-key fingerprint 0EBFCD88 \
    && add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

RUN apt-get update && apt-get install -y docker-ce

# Setup UWSGI install
RUN /usr/sbin/useradd --system --no-log-init --no-create-home --shell /sbin/nologin --home-dir /var/run/uwsgi uwsgi

ADD . /opt/threatkb
WORKDIR /opt/threatkb
ADD uwsgi.yaml /etc/uwsgi.yaml

# Install Python Dependencies
RUN pip install virtualenv && virtualenv env && env/bin/pip install -r requirements.txt

# Install Node Dependencies
RUN npm install -g bower && ln -s /usr/bin/nodejs /usr/bin/node && bower install --allow-root

# Generate Version File
RUN git log -1 --format="%H" > version
RUN git log -1 --format="%cE" >> version
RUN git log -1 --format="%ci" >> version
RUN chmod 744 *.sh

CMD ["/opt/threatkb/docker-entrypoint.sh"]
