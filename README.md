# NOTE: THIS REPO IS IN AN ALPHA STATE

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
    - Create MySQL database: `create database threatkb;`
    - Create MySQL user: `CREATE USER 'threatkb'@'localhost' IDENTIFIED BY 'password';`
    - Allow permissions: `GRANT ALL PRIVILEGES ON threatkb . * TO 'threatkb'@'localhost';`
    - Flush privileges: `FLUSH PRIVELEGES;` 
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

### Running ThreatKB  
It's best to run the application and it's Python virtualenv within a screen session to ensure ThreatKB continues to run.

**Note:** Within screen, Ctrl+a+d will dettach your session and return you to your normal shell. To return to the  screen session, run `screen -r threatkb`

1. Start a screen session for the application to run within:
    - `cd /opt/ThreatKB && screen -dmS threatkb InQuest_ThreatKB`
2. Inside of screen, start the virtualenv:
    - `source flask/bin/activate`
3. Start the celery workers:
    - `celery -A app.celeryapp.celery work -E`
    - This is required in order for testing against your clean corpus of files
4. Build the database tables and columns:
    - `flask/bin/python manage.py db upgrade`
4. Run the application:
    - `flask/bin/python run.py`
    - Follow the instructions below on creating your first Admin user before continuing to next step
5. Open your browser to http://127.0.0.1:5000/#!/login and get started using ThreatKB!


### Admin User Creation
1. Hash your password for MySQL kb_users table:
    - `flask/bin/python hash_pass.py yourSecretPassword`
2. Connect to MySQL instance and insert your admin user (replace values below as needed):
    - `sql INSERT INTO kb_users (email, password, admin) VALUES ("user@domain.com", "<hashed password>, 1, 1);`


## Docker Installation  
1. Edit docker-compose.yml if you change to change defaults such as ports or credentials
2. Build the Docker image: `docker build -t threatkb .`
3. Execute docker-compuse: `docker-compose up`
4. Open your browser to htp://127.0.0.1:5000/#!/login

**Example output:**
```
$ docker-compose up
-Starting inquestkb_db_1 ... 	
-Starting inquestkb_db_1 ... done
-Recreating inquestkb_threatkb_1 ... 	
-Recreating inquestkb_threatkb_1 ... done
-Attaching to inquestkb_db_1, inquestkb_threatkb_1
-....snip...
-threatkb_1  |  * Debugger is active!
-threatkb_1  |  * Debugger PIN: 212-674-856
```

## Databases  
Please see ThreatKB/migrations/README documentation

## Release Logic  
Releases are controlled by artifact states. States are configurable in the States admin section. There are 4 kinds of states:
1. Release state - This is the state artifacts go into when you want to release them.
2. Staging state - This is the state artifacts go into when they are being prepped for release. Any signature that is in the release state and is modified automatically get put into the staging state by the system. Only relevant for signatures.
3. Retired state - This excludes a previously released artifact from future releases. Only relevant for signatures.
4. Any other state - Any other state has no significance on releases. These will not be included in releases.

The Release, Staging, and Retired states must be configured in the admin section *before* you can generate a release. If they are not, the system will error out.

When a release is created, the system first pulls all signatures that are in the release state. Then, it gathers all signatures that are in the staging state and checks their revision history for the most recently released revision that is in the release state. If it finds it, it will include it in the release. If it does not find any previously released revisions, it will skip the signature.

## Thank You
ThreatKB utilizes Plyara to parse yara rules into python dictionaries. A huge thank you to the Plyara team! Links to the project are below:

https://github.com/8u1a/plyara
https://github.com/8u1a/plyara/blob/master/LICENSE
