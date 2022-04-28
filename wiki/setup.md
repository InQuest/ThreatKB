### Docker


1. Checkout staging branch:
    - `git checkout -b staging origin/staging`
2. Make data diretories:
    - `mkdir db_data`
    - `mkdir files`
3. Start:
    - `docker-compose up -d`
4. Navigate to the app:
    - `http://localhost:5000`


### Pre-requisites

Tested on Ubuntu Linux 14.04 -> 18.10

1. Install system dependencies and libraries:
    - `sudo apt-get install git screen libffi-dev libssl-dev libsqlite3-dev libmysqlclient-dev`
2. Install Python and associated packages:
    - `sudo apt-get install python2.7 python-pip python-dev libpython-dev`
3. Install Python virtualenv library:
    - `pip install virtualenv`
3. Install databases:
    - `sudo apt-get install mysql-server redis-server`
4. Install front-end packages:
    - `sudo apt-get install nodejs npm && npm install -g bower`
    - On some systems, nodejs is installed as either `/usr/bin/node` or `/usr/bin/nodejs`, if it is installed as `/usr/bin/nodejs` simply run the command `sudo cp /usr/bin/nodejs /usr/bin/node` for the npm install command to work properly

**Note:** If you are running on CentOS, install these dependencies:
`yum install MySQL-python libffi-devel mysql mysql-devel mysql-lib`

### System Prep  
1. Create system user: `sudo useradd -d /opt/ThreatKB -s /bin/bash -m -U threatkb`
2. Clone repo: `sudo git clone -b master https://github.com/InQuest/ThreatKB.git /opt/ThreatKB/install`
3. Fix permissions of /opt/ThreatKB if needed: `sudo chown -R threatkb:threatkb /opt/ThreatKB`
4. In MySQL shell as root user:
    - Create MySQL database: `CREATE DATABASE threatkb;`
    - Create MySQL user: `CREATE USER 'threatkb'@'localhost' IDENTIFIED BY 'password';`
    - Allow permissions: `GRANT ALL PRIVILEGES ON threatkb . * TO 'threatkb'@'localhost';`
    - Flush privileges: `FLUSH PRIVILEGES;`
5. Update SQL config in /opt/ThreatKB/config.py parameters:
    - SQL_HOST
    - SQL_USERNAME
    - SQL_PASSWORD

### Application Install
**Note:** These steps and the execution of ThreatKB should be ran under the `threatkb` local user you created earlier

1. Run `./install.sh`
    - Setups a Python virtual environment in the directory `/opt/ThreatKB/flask`
    - Installs required node libraries for front-end

By default Flask will listen on 127.0.0.1:5000, if you want to change this modify the `app.run()` command inside `/opt/ThreatKB/run.py`

----
#### Setup Complete

Now that you are finished with setup, head to [Getting Started](getting-started.md).
