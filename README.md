
This project uses Yeoman for scaffolding. Specifically, we are using the angular-flask generator. More information on that found here.

https://github.com/rayokota/generator-angular-flask

## Pre-requisites
1. Python 2.7
    ```
    # Using Homebrew on Mac
    $ brew install python
    ```
1. Virtualenv
    ```
    $ pip install virtualenv
    ```
1. Install NPM
    ```
    # Using Homebrew on Mac
    $ brew install node
    ```
1. Install Bower
    ```
    $ npm install -g bower
    ```

## Installation
```
~ $ mkdir -p InQuest/
~ $ cd InQuest
InQuest $ git clone -b staging git@github.com:InQuest/ThreatKB.git
InQuest $ cd ThreatKB
ThreatKB (staging) $ ./install.sh
ThreatKB (staging) $ flask/bin/pip install -r requirements.txt
ThreatKB (staging) $ npm install -g yo generator-angular-flask
ThreatKB (staging) $ bower install
ThreatKB (staging) $ grunt server
```

## Run
```
ThreatKB (staging) $ flask/bin/python run.py
ThreatKB (staging) $ grunt server
```

## Miscellaneous

### Hashing password for insert in kb_users table
```
(flask) ThreatKB (staging) $ ./hash_pass.py abc123
$2b$12$Kfana8UbHxYwrksmXS5NiudRTG/m0hRloUwN/hc1mxl/dx5fPTwMC
```

### Inserting Test User in DB
```sql
INSERT INTO kb_users (email, password, admin)
VALUES ('test@test.com', '<hashed pass>', 1);
```
