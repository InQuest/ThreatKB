# Getting Started

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
    - `INSERT INTO kb_users (email, password, admin, active) VALUES ('user@domain.com', '<hashed password>', 1, 1);`


----
#### Installation Complete

ThreatKB is now running. To learn more about this project, explore the [wiki](README.md).
