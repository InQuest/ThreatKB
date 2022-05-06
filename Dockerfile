FROM ubuntu:20.04

# Update OS Packages, Install OS Dependencies (Do this in one line to ensure Update always happens)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true apt-get install -y git libsqlite3-dev python3.8 python3-pip npm libffi-dev libssl-dev mysql-client \
    libmysqlclient-dev python3-dev libpython3-dev git yara apt-transport-https ca-certificates curl \
    software-properties-common libpcre3 libpcre3-dev

# Setup UWSGI Installation
RUN /usr/sbin/useradd --system --no-log-init --no-create-home --shell /sbin/nologin --home-dir /var/run/uwsgi uwsgi
COPY ./uwsgi.yaml /etc/uwsgi.yaml

# Install Code Dependencies
WORKDIR /opt/threatkb
COPY package.json .bowerrc bower.json Gruntfile.js requirements.txt ./

# Install Python Dependencies
RUN /usr/bin/pip3 install --upgrade pip & /usr/bin/pip3 install virtualenv
RUN /usr/local/bin/virtualenv -p /usr/bin/python3.8 env
RUN env/bin/pip3 install -r requirements.txt

# Install Node Dependencies
RUN npm install -g bower && bower install --allow-root

# Add Package Files
COPY . /opt/threatkb

# Generate Version File
RUN git log -1 --format="%H" > version
RUN git log -1 --format="%cE" >> version
RUN git log -1 --format="%ci" >> version
RUN chmod 744 *.sh

CMD ["/opt/threatkb/docker-entrypoint.sh"]
