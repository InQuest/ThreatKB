## Pre-requisites
# Instructions in Ubuntu Linux

1. Python 2.7
    ```
    $ apt-get install python2.7
    ```
1. Virtualenv
    ```
    $ pip install virtualenv
    ```
1. Install NPM
    ```
    $ apt-get install nodejs
    ```
1. Install Bower
    ```
    $ npm install -g bower
    ```
1. Install Redis
    ```
    $ apt-get install redis-server
    ```
1. Install MySQL
    ```
    $ apt-get install mysql-server
    ```

# Additional Dependencies for CentOS
```
yum install MySQL-python libffi-devel mysql mysql-devel mysql-lib
```

## Installation
```
~ $ INQUEST_HOME='/opt/WhereverYouWantToPutIt'
~ $ mkdir -p ${INQUEST_HOME}
~ $ cd ${INQUEST_HOME}
InQuest $ git clone -b master git@github.com:InQuest/ThreatKB.git
InQuest $ cd ThreatKB
ThreatKB (master) $ mysql -u root -p{YOURPASS} create database threatkb;

Edit config.py with the appropriate SQLALCHEMY_DATABASE_URI

ThreatKB (master) $ ./install.sh
```

## Run
```
Edit run.py with 'app.run(host="0.0.0.0",debug=True)' if you want to listen on all interfaces. Listens on port 5000 by default.

ThreatKB (master) $ screen -t INQUEST_APP
ThreatKB (master) $ flask/bin/python run.py

Ctrl+A, Ctrl+D to dettach screen
```

## Databases
Please see ThreatKB/migrations/README.

## Miscellaneous

### celery
Requires running inside virtualenv. Needs to be running in order for testing Clean Corpus of files.
```
ThreatKB (staging) $ source flask/bin/activate
(flask) ThreatKB (staging) $ celery -A app.celeryapp.celery worker -E
```

### Hashing password for insert in kb_users table
```
(flask) ThreatKB (master) $ flask/bin/python hash_pass.py abc123
$2b$12$Kfana8UbHxYwrksmXS5NiudRTG/m0hRloUwN/hc1mxl/dx5fPTwMC
```

### Inserting Test User in DB
```sql
INSERT INTO kb_users (email, password, admin)
VALUES ('test@test.com', '<hashed pass>', 1);
```

## Docker Instructions
```
Edit docker-compose.yml if you want to change default ports, credentials, etc. Once the following is complete, visit http://127.0.0.1:5000/!#/login in your browser.

(flask) danny@dannys-MBP InquestKB (staging) $ docker build -t threatkb .
....snip....
Successfully built 9a16b1f1c55b
Successfully tagged threatkb:latest
(flask) danny@dannys-MBP InquestKB (staging) $ docker-compose up
Starting inquestkb_db_1 ... 
Starting inquestkb_db_1 ... done
Recreating inquestkb_threatkb_1 ... 
Recreating inquestkb_threatkb_1 ... done
Attaching to inquestkb_db_1, inquestkb_threatkb_1
....snip...
threatkb_1  |  * Debugger is active!
threatkb_1  |  * Debugger PIN: 212-674-856
```

