


<p align="center">
    <img src="wiki/res/inquest_logo.svg"></img>
</p>

### Running ThreatKB  
It's best to run the application and it's Python virtualenv within a screen session to ensure ThreatKB continues to run.
  
**Note:** Within screen, Ctrl+a+d will detach your session and return you to your normal shell. To return to the  screen session, run `screen -list` and look for the "Inquest_ThreatKB" entry followed by its PID then use `screen -r InQuest_ThreatKB.<PID>` to reattach.
  
1. Start a screen session for the application to run within:
    - `screen -t InQuest_ThreatKB`
    - Make sure you are inside of the `/opt/ThreatKB` directory within screen
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


### NOTE: THIS REPO IS IN AN ALPHA STATE


### Admin User Creation
1. Hash your password for MySQL kb_users table:
    - `flask/bin/python hash_pass.py yourSecretPassword`
2. Connect to MySQL instance and insert your admin user (replace values below as needed):
    - `sql INSERT INTO kb_users (email, password, admin, active) VALUES ("user@domain.com", "<hashed password>", 1, 1);`


ThreatKB is a knowledge base workflow management dashboard for Yara rules and C2 artifacts. Rules are categorized and used to denote intent, severity, and confidence on accumulated artifacts.

To start using ThreatKB, follow our [guide](wiki/setup.md).

  ---  

## Table of Contents

* [Setup ThreatKB](wiki/setup.md)
  + [Pre-requisites](wiki/setup.md#pre-requisites)
  + [System Prep](wiki/setup.md#system-prep)
* [Getting Started](wiki/getting-started.md)
  + [Application Install](wiki/getting-started.md#application-install)
  + [Running ThreatKB](wiki/getting-started.md#running-threatkb)
  + [Admin User Creation](wiki/getting-started.md#admin-user-creation)
* [Docker Installation](wiki/docker.md)
* [Databases](wiki/db-struct.md)
* [Documentation](wiki/documentation.md)
* [FAQ](wiki/faq.md)



## Thank You
ThreatKB utilizes Plyara to parse yara rules into python dictionaries. A huge thank you to the Plyara team! Links to the project are below:

https://github.com/8u1a/plyara
https://github.com/8u1a/plyara/blob/master/LICENSE

When a release is created, the system first pulls all signatures that are in the release state. Then, it gathers all signatures that are in the staging state and checks their revision history for the most recently released revision that is in the release state. If it finds it, it will include it in the release. If it does not find any previously released revisions, it will skip the signature.

