# NOTE: THIS REPO IS IN A PRE-RELEASE STATE

  * [Setup and run ThreatKB](#setup-and-run-threatkb)
    + [Pre-requisites](#pre-requisites)
    + [System Prep](#system-prep)
    + [Application Install](#application-install)
    + [Running ThreatKB](#running-threatkb)
    + [Admin User Creation](#admin-user-creation)
  * [Docker Installation](#docker-installation)
  * [Databases](#databases)
  
  ---  

## Setup and run ThreatKB
### Pre-requisites
Tested on Ubuntu Linux 14.04 -> 16.04

1. Install system dependencies and libraries:
    - `sudo apt-get install git screen libffi-dev libssl-dev libsqlite3-dev`
2. Install Python and associated packages:
    - `sudo apt-get install python2.7 python-pip python-dev libpython-dev`
3. Install Python virtualenv library:
    - `pip install virtualenv`
3. Install databases:
    - `sudo apt-get install mysql-server redis-server`
4. Install front-end packages:
    - `sudo apt-get install nodejs && npm install -g bower`

**Note:** If you are running on CentOS, install these dependencies:
`yum install MySQL-python libffi-devel mysql mysql-devel mysql-lib`

### System Prep  
1. Create system user: `sudo useradd -d /opt/ThreatKB -s /bin/bash -m -U`
2. Clone repo: `sudo git clone -b master git@github.com:InQuest/ThreatKB.git /opt/ThreatKB`
3. Fix permissions of /opt/ThreatKB if needed: `sudo chown -R threatkb:threatkb /opt/ThreatKB`
4. Create MySQL database: `mysql -u root -p{your password} create database threatkb;`
5. Update SQL config in /opt/ThreatKB/config.py parameters:
    - SQL_HOST
    - SQL_USERNAME
    - SQL_PASSWORD

### Application Install 
1. Run `./install.sh`
    - Setups a Python virtual environment in the directory `/opt/ThreatKB/flask`
    - Installs required node libraries for front-end

By default Flask will listen on 127.0.0.1:5000, if you want to change this modify the `app.run()` command inside `/opt/ThreatKB/run.py`

### Running ThreatKB  
It's best to run the application and it's Python virtualenv within a screen session to ensure ThreatKB continues to run.
  
**Note:** Within screen, Ctrl+a+d will dettach your session and return you to your normal shell. To return to the  screen session, run `screen -list` and look for the "Inquest_ThreatKB" entry followed by its PID then use `screen -r InQuest_ThreatKB.<PID>` to reattach.
  
1. Start a screen session for the application to run within:
    - `screen -t InQuest_ThreatKB`
    - Make sure you are inside of the `/opt/ThreatKB` directory within screen
2. Inside of screen, start the virtualenv:
    - `source flask/bin/activate`
3. Start the celery workers:
    - `celery -A app.celeryapp.celery work -E`
    - This is required in order for testing against your clean corpus of files
4. Build the database tables and columns:
    - `flask/bin/python manage.db upgrade`
4. Run the application:
    - `flask/bin/python run.py`
    - Follow the instructions below on creating your first Admin user before continuing to next step
5. Open your browser to http://127.0.0.1:5000/#1/login and get started using ThreatKB!


### Admin User Creation
1. Hash your password for MySQL kb_users table:
    - `flask/bin/python hash_pass.py yourSecretPassword`
2. Connect to MySQL instance and insert your admin user (replace values below as needed):
    - `sql INSERT INTO kb_users (email, password, admin) VALUES ("user@domain.com", "<hashed password>, 1, 1);`


## Docker Installation  
1. Edit docker-compose.yml if you change to change defaults such as ports or credentials
2. Build the Docker image: `docker build -t threatkb .`
3. Execute docker-compuse: `docker-compuse up`
4. Open your browser to htp://127.0.0.1:5000/#1/login

## Databases  
Please see ThreatKB/migrations/README documentation

