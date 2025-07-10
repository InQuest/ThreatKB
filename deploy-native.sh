#!/bin/bash
#
# ThreatKB Native Deployment Script
# This script installs and configures ThreatKB directly on a Linux server
# with options for local or remote MySQL database.
#

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration variables
MYSQL_INSTALL_TYPE=""   # Will be set to "local" or "remote"
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
MYSQL_USER="threatkb"
MYSQL_PASSWORD=""
MYSQL_ROOT_PASSWORD=""
MYSQL_DATABASE="threatkb"
# SERVER_NAME is the domain name or IP address for nginx (e.g., "example.com" or "192.168.1.100")
SERVER_NAME="$(hostname -I | awk '{print $1}')"
SECRET_KEY="$(openssl rand -hex 24)"
SECURITY_SALT="$(openssl rand -hex 16)"
# Set to "true" if you want to skip git clone (files already exist)
SKIP_GIT_CLONE="false"

# Installation paths
INSTALL_DIR="/opt/threatkb"
LOG_DIR="/var/log/threatkb"
UWSGI_LOG_DIR="/var/log/uwsgi"

# Print section header
print_section() {
    echo -e "\n${GREEN}=== $1 ===${NC}\n"
}

# Print status message
print_status() {
    echo -e "${YELLOW}>>> $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script as root or with sudo${NC}"
    exit 1
fi

print_section "ThreatKB Deployment Configuration"

# MySQL Installation Choice
echo -e "${YELLOW}Choose MySQL installation option:${NC}"
echo "1) Install MySQL locally (recommended for new deployments)"
echo "2) Use existing remote MySQL server"
echo ""
while true; do
    read -p "Enter your choice [1-2]: " mysql_choice
    case $mysql_choice in
        1)
            MYSQL_INSTALL_TYPE="local"
            MYSQL_HOST="localhost"
            # Generate secure passwords
            MYSQL_ROOT_PASSWORD="$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-25)"
            MYSQL_PASSWORD="$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-25)"
            echo -e "${GREEN}✓ Local MySQL installation selected${NC}"
            echo -e "${YELLOW}Generated secure passwords will be saved to /opt/threatkb/.mysql_credentials${NC}"
            break
            ;;
        2)
            MYSQL_INSTALL_TYPE="remote"
            echo -e "${GREEN}✓ Remote MySQL selected${NC}"
            echo ""
            read -p "Enter MySQL host: " MYSQL_HOST
            read -p "Enter MySQL port [3306]: " MYSQL_PORT
            MYSQL_PORT=${MYSQL_PORT:-3306}
            read -p "Enter MySQL username: " MYSQL_USER
            read -sp "Enter MySQL password: " MYSQL_PASSWORD
            echo ""
            read -p "Enter MySQL database name [threatkb]: " MYSQL_DATABASE
            MYSQL_DATABASE=${MYSQL_DATABASE:-threatkb}
            break
            ;;
        *)
            echo -e "${RED}Invalid choice. Please enter 1 or 2.${NC}"
            ;;
    esac
done

# Server configuration
echo ""
read -p "Enter server name/IP for nginx [$SERVER_NAME]: " input_server_name
SERVER_NAME=${input_server_name:-$SERVER_NAME}
echo -e "${YELLOW}Note: SERVER_NAME is used for nginx configuration. Use your domain name or server IP address.${NC}"

print_section "System Update and Package Installation"

# Update system packages
print_status "Updating system packages..."
apt update
apt upgrade -y

# Install required system dependencies
print_status "Installing system dependencies..."
apt install -y python3.10 python3.10-venv python3.10-dev build-essential git
apt install -y nginx redis-server uwsgi uwsgi-plugin-python3
apt install -y npm nodejs curl

# Install MySQL based on user choice
if [ "$MYSQL_INSTALL_TYPE" == "local" ]; then
    print_status "Installing MySQL server locally..."
    # Set MySQL root password non-interactively
    echo "mysql-server mysql-server/root_password password $MYSQL_ROOT_PASSWORD" | debconf-set-selections
    echo "mysql-server mysql-server/root_password_again password $MYSQL_ROOT_PASSWORD" | debconf-set-selections
    apt install -y mysql-server mysql-client libmysqlclient-dev
    
    # Start and enable MySQL service
    systemctl start mysql
    systemctl enable mysql
    
    print_status "Configuring MySQL database and user..."
    # Create database and user
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF
CREATE DATABASE IF NOT EXISTS $MYSQL_DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON $MYSQL_DATABASE.* TO '$MYSQL_USER'@'localhost';
FLUSH PRIVILEGES;
EOF
    
    # Save credentials to file
    mkdir -p /opt/threatkb
    cat > /opt/threatkb/.mysql_credentials <<EOF
# MySQL Credentials for ThreatKB
# Generated on $(date)
MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD"
MYSQL_USER="$MYSQL_USER"
MYSQL_PASSWORD="$MYSQL_PASSWORD"
MYSQL_DATABASE="$MYSQL_DATABASE"
MYSQL_HOST="$MYSQL_HOST"
MYSQL_PORT="$MYSQL_PORT"
EOF
    chmod 600 /opt/threatkb/.mysql_credentials
    chown root:root /opt/threatkb/.mysql_credentials
    
    echo -e "${GREEN}✓ MySQL server installed and configured${NC}"
    echo -e "${YELLOW}MySQL credentials saved to: /opt/threatkb/.mysql_credentials${NC}"
else
    print_status "Installing MySQL client for remote connection..."
    apt install -y mysql-client libmysqlclient-dev
fi

print_section "Application Setup"

# Create application directory
print_status "Creating application directory..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Clone the repository or use existing files
if [ "$SKIP_GIT_CLONE" = "true" ]; then
    print_status "Skipping git clone - using existing files in $INSTALL_DIR"
    if [ ! -d "$INSTALL_DIR" ] || [ ! -f "$INSTALL_DIR/requirements.txt" ]; then
        echo -e "${RED}Error: ThreatKB files not found in $INSTALL_DIR. Please ensure the files are uploaded first.${NC}"
        exit 1
    fi
else
    print_status "Cloning ThreatKB repository..."
    if [ -d "$INSTALL_DIR/.git" ]; then
        print_status "Repository already exists, updating..."
        cd $INSTALL_DIR
        git pull
    else
        git clone $THREATKB_REPO $INSTALL_DIR
        cd $INSTALL_DIR
        git checkout $THREATKB_BRANCH
    fi
fi

# Create Python virtual environment
print_status "Setting up Python virtual environment..."
python3.10 -m venv env
source env/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install frontend dependencies
print_status "Installing frontend dependencies..."
npm install -g bower
bower install --allow-root

print_section "Configuration"

# Create config.py file
print_status "Creating application configuration..."
cat > $INSTALL_DIR/config.py << EOF
import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = '${SECRET_KEY}'
SECURITY_PASSWORD_SALT = '${SECURITY_SALT}'

# Redis configuration
REDIS_URL = 'redis://localhost:6379'
REDIS_BROKER_URL = 'redis://localhost:6379/0'
REDIS_TASK_SERIALIZER = 'json'
REDIS_RESULT_SERIALIZER = 'json'
REDIS_ACCEPT_CONTENT = ['json']

# File storage
FILE_STORE_PATH = '${INSTALL_DIR}/files'

# Logging
LOGGING_LEVEL = 10  # DEBUG level
EOF

# Create log directories
print_status "Creating log directories..."
mkdir -p $LOG_DIR $UWSGI_LOG_DIR
chmod 755 $LOG_DIR $UWSGI_LOG_DIR

print_section "Database Setup"

# Test database connection
if [ "$MYSQL_INSTALL_TYPE" == "local" ]; then
    print_status "Testing local database connection..."
    if mysql -u $MYSQL_USER -p"$MYSQL_PASSWORD" -e "USE $MYSQL_DATABASE"; then
        print_status "Local database connection successful"
    else
        echo -e "${RED}Error: Cannot connect to local database $MYSQL_DATABASE.${NC}"
        exit 1
    fi
else
    print_status "Testing remote database connection..."
    if mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p"$MYSQL_PASSWORD" -e "USE $MYSQL_DATABASE"; then
        print_status "Remote database connection successful"
    else
        echo -e "${RED}Error: Cannot connect to remote database $MYSQL_DATABASE.${NC}"
        echo -e "${RED}Please verify your database credentials and ensure the database exists.${NC}"
        exit 1
    fi
fi

# Initialize database schema
print_status "Initializing database schema..."
cd $INSTALL_DIR
source env/bin/activate
export FLASK_APP=app
flask db upgrade

# Create default admin user if it doesn't exist
print_status "Creating default admin user..."
python3 << EOF
import sys
sys.path.insert(0, '$INSTALL_DIR')
from app import create_app, db
from app.models import KbUser
import hashlib

app = create_app()
with app.app_context():
    # Check if admin user exists
    admin_user = KbUser.query.filter_by(email='admin@inquest.net').first()
    if not admin_user:
        # Create admin user
        password_hash = hashlib.sha256('b5vXcqzUtn4suyS'.encode()).hexdigest()
        admin_user = KbUser(
            email='admin@inquest.net',
            password=password_hash,
            admin=True,
            active=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print('Admin user created successfully')
    else:
        print('Admin user already exists')
EOF

print_section "uWSGI Configuration"

# Create uWSGI configuration
print_status "Configuring uWSGI..."
mkdir -p /etc/uwsgi/apps-available /etc/uwsgi/apps-enabled

cat > /etc/uwsgi/apps-available/threatkb.ini << EOF
[uwsgi]
uid = www-data
gid = www-data
master = true
workers = 10
auto-procname = true
close-on-exec = true
reaper = true
max-requests = 1000
module = wsgi
callable = application
virtualenv = ${INSTALL_DIR}/env
python-path = ${INSTALL_DIR}
ignore-sigpipe = true
ignore-write-errors = true
http-timeout = 600
harakiri = 600
socket = /tmp/threatkb.sock
chmod-socket = 666
logto = ${UWSGI_LOG_DIR}/threatkb.log
log-maxsize = 50000000
log-backupname = ${UWSGI_LOG_DIR}/threatkb.log.old
logformat = [pid: %(pid)|app: -|req: -/-] %(addr) (%(user)) {%(vars) vars in %(pktsize) bytes} [%(ctime)] %(method) %(uri) => generated %(rsize) bytes in %(msecs) msecs (%(proto) %(status)) %(headers) headers in %(hsize) bytes (%(switches) switches on core %(core))
req-logger = file:${UWSGI_LOG_DIR}/requests.log
memory-report = true
EOF

# Create symbolic link to enable the app
ln -sf /etc/uwsgi/apps-available/threatkb.ini /etc/uwsgi/apps-enabled/

# Create uWSGI service
print_status "Creating uWSGI service..."
cat > /etc/systemd/system/uwsgi.service << 'EOF'
[Unit]
Description=uWSGI Emperor service
After=syslog.target network.target

[Service]
ExecStart=/usr/bin/uwsgi --emperor /etc/uwsgi/apps-enabled --plugin python3
Restart=always
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all

[Install]
WantedBy=multi-user.target
EOF

print_section "Nginx Configuration"

# Configure Nginx
print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/threatkb << EOF
server {
    listen 80;
    server_name ${SERVER_NAME};

    # Logging configuration
    access_log /var/log/nginx/threatkb-access.log;
    error_log /var/log/nginx/threatkb-error.log warn;

    # Increase client max body size for file uploads
    client_max_body_size 100M;

    # Proxy timeouts
    proxy_connect_timeout 120s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    proxy_buffering off;
    proxy_request_buffering off;

    # Main application
    location / {
        include uwsgi_params;
        uwsgi_pass unix:/tmp/threatkb.sock;
        uwsgi_param Host \$host;
        uwsgi_param X-Real-IP \$remote_addr;
        uwsgi_param X-Forwarded-For \$proxy_add_x_forwarded_for;
        uwsgi_param X-Forwarded-Proto \$scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static/ {
        alias ${INSTALL_DIR}/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/threatkb /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site if exists

# Test Nginx configuration
nginx -t

print_section "Celery Worker Configuration"

# Configure Celery Worker Service
print_status "Configuring Celery worker service..."
cat > /etc/systemd/system/threatkb-celery.service << EOF
[Unit]
Description=ThreatKB Celery Worker
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/env/bin"
ExecStart=${INSTALL_DIR}/env/bin/celery -A app.celery worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

print_section "Setting Permissions"

# Set proper permissions
print_status "Setting proper file permissions..."
chown -R www-data:www-data $INSTALL_DIR
chown -R www-data:www-data $LOG_DIR $UWSGI_LOG_DIR

print_section "Starting Services"

# Reload systemd
systemctl daemon-reload

# Enable and start services
print_status "Enabling and starting services..."
systemctl enable redis-server
systemctl enable uwsgi
systemctl enable threatkb-celery
systemctl enable nginx

systemctl restart redis-server
systemctl restart uwsgi
systemctl restart threatkb-celery
systemctl restart nginx

print_section "Deployment Complete"

echo -e "\n${GREEN}=== ThreatKB Deployment Complete! ===${NC}\n"
echo -e "Access your ThreatKB instance at: ${YELLOW}http://${SERVER_NAME}/${NC}"
echo -e "Default login credentials:"
echo -e "  - Username: admin@inquest.net"
echo -e "  - Password: b5vXcqzUtn4suyS"
echo -e "\n${YELLOW}IMPORTANT: Change the default password after first login!${NC}"

# Show MySQL-specific information
if [ "$MYSQL_INSTALL_TYPE" == "local" ]; then
    echo -e "\n${GREEN}MySQL Database (Local Installation):${NC}"
    echo -e "  - Database: $MYSQL_DATABASE"
    echo -e "  - User: $MYSQL_USER"
    echo -e "  - Host: $MYSQL_HOST:$MYSQL_PORT"
    echo -e "  - Credentials saved to: ${YELLOW}/opt/threatkb/.mysql_credentials${NC}"
    echo -e "  - MySQL service: $(systemctl is-active mysql)"
    echo -e "\n${YELLOW}MySQL Management:${NC}"
    echo -e "  - sudo systemctl restart mysql         # Restart MySQL server"
    echo -e "  - mysql -u $MYSQL_USER -p             # Connect to database"
    echo -e "  - cat /opt/threatkb/.mysql_credentials # View saved credentials"
else
    echo -e "\n${GREEN}MySQL Database (Remote Connection):${NC}"
    echo -e "  - Database: $MYSQL_DATABASE"
    echo -e "  - User: $MYSQL_USER"
    echo -e "  - Host: $MYSQL_HOST:$MYSQL_PORT"
    echo -e "  - Connection: Remote server"
fi

echo -e "\n${GREEN}Service Status:${NC}"
echo -e "  - uWSGI: $(systemctl is-active uwsgi)"
echo -e "  - Nginx: $(systemctl is-active nginx)"
echo -e "  - Redis: $(systemctl is-active redis-server)"
echo -e "  - Celery: $(systemctl is-active threatkb-celery)"

echo -e "\n${GREEN}Log Files:${NC}"
echo -e "  - Application: /var/log/uwsgi/threatkb.log"
echo -e "  - Nginx Access: /var/log/nginx/threatkb-access.log"
echo -e "  - Nginx Error: /var/log/nginx/threatkb-error.log"
echo -e "  - Celery: /var/log/threatkb-celery.log"

echo -e "\n${GREEN}Service Management:${NC}"
echo -e "  - sudo systemctl restart uwsgi         # Restart application"
echo -e "  - sudo systemctl restart nginx         # Restart web server"
echo -e "  - sudo systemctl restart redis-server  # Restart Redis"
echo -e "  - sudo systemctl restart threatkb-celery  # Restart background tasks"

echo -e "\n${GREEN}Troubleshooting:${NC}"
echo -e "  - sudo tail -f /var/log/uwsgi/threatkb.log    # View app logs"
echo -e "  - sudo systemctl status uwsgi nginx redis    # Check service status"
echo -e "  - sudo nginx -t                              # Test nginx config"

echo -e "\n${YELLOW}Security Recommendations:${NC}"
echo -e "  - Change default admin password immediately"
echo -e "  - Configure HTTPS/SSL for production use"
echo -e "  - Set up firewall rules (ufw enable)"
echo -e "  - Regular security updates (apt update && apt upgrade)"
if [ "$MYSQL_INSTALL_TYPE" == "local" ]; then
    echo -e "  - Secure MySQL installation (mysql_secure_installation)"
    echo -e "  - Backup MySQL credentials file securely"
fi

echo -e "\n${GREEN}Optional: Add Datadog APM Integration${NC}"
echo -e "For production monitoring, you can add APM integration:"
echo -e "  cd /path/to/datadog-apm-integration"
echo -e "  sudo ./install-ddtrace-apm.sh"

echo -e "\n${GREEN}Deployment Summary:${NC}"
echo -e "  - ThreatKB Application: ✓ Installed"
echo -e "  - MySQL Database: ✓ $([ "$MYSQL_INSTALL_TYPE" == "local" ] && echo "Local" || echo "Remote")"
echo -e "  - Web Server (Nginx): ✓ Configured"
echo -e "  - Application Server (uWSGI): ✓ Running"
echo -e "  - Background Tasks (Celery): ✓ Running"
echo -e "  - Cache (Redis): ✓ Running"
echo -e "\n${GREEN}🎉 ThreatKB is ready to use! 🎉${NC}"
