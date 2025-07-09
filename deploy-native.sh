#!/bin/bash
#
# ThreatKB Native Deployment Script
# This script installs and configures ThreatKB directly on a Linux server
# without Docker, connecting to a remote MySQL database.
#

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration variables - MODIFY THESE
MYSQL_HOST="your-mysql-host"
MYSQL_PORT="3306"
MYSQL_USER="your-mysql-user"
MYSQL_PASSWORD="your-mysql-password"
MYSQL_DATABASE="threatkb"
SERVER_NAME="your-server-name"
SECRET_KEY="$(openssl rand -hex 24)"
SECURITY_SALT="$(openssl rand -hex 16)"
THREATKB_REPO="https://github.com/your-repo/ThreatKB.git"
THREATKB_BRANCH="main"

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

# Prompt for configuration if not provided as environment variables
if [ "$MYSQL_HOST" == "your-mysql-host" ]; then
    read -p "Enter MySQL host: " MYSQL_HOST
    read -p "Enter MySQL port [3306]: " MYSQL_PORT
    MYSQL_PORT=${MYSQL_PORT:-3306}
    read -p "Enter MySQL username: " MYSQL_USER
    read -sp "Enter MySQL password: " MYSQL_PASSWORD
    echo ""
    read -p "Enter MySQL database name [threatkb]: " MYSQL_DATABASE
    MYSQL_DATABASE=${MYSQL_DATABASE:-threatkb}
    read -p "Enter server name for nginx [$(hostname)]: " SERVER_NAME
    SERVER_NAME=${SERVER_NAME:-$(hostname)}
fi

print_section "System Update and Package Installation"

# Update system packages
print_status "Updating system packages..."
apt update
apt upgrade -y

# Install required system dependencies
print_status "Installing system dependencies..."
apt install -y python3.10 python3.10-venv python3.10-dev build-essential git
apt install -y nginx redis-server uwsgi uwsgi-plugin-python3
apt install -y default-mysql-client default-libmysqlclient-dev
apt install -y npm nodejs curl

print_section "Application Setup"

# Create application directory
print_status "Creating application directory..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Clone the repository
print_status "Cloning ThreatKB repository..."
if [ -d "$INSTALL_DIR/.git" ]; then
    print_status "Repository already exists, updating..."
    git pull
else
    git clone $THREATKB_REPO $INSTALL_DIR
    git checkout $THREATKB_BRANCH
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
print_status "Testing database connection to existing database..."
if mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD -e "USE $MYSQL_DATABASE"; then
    print_status "Database connection successful"
else
    echo -e "${RED}Error: Cannot connect to database $MYSQL_DATABASE. Please verify your database credentials and ensure the database exists.${NC}"
    exit 1
fi

# Skip database migrations
print_status "Skipping database migrations as requested - using existing database structure"

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
module = app
callable = app
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

echo -e "${GREEN}ThreatKB has been successfully deployed!${NC}"
echo -e "You can access the application at: http://${SERVER_NAME}"
echo -e "\nImportant paths:"
echo -e "  - Application: ${INSTALL_DIR}"
echo -e "  - Logs: ${LOG_DIR}"
echo -e "  - uWSGI Logs: ${UWSGI_LOG_DIR}"
echo -e "  - Nginx Logs: /var/log/nginx/threatkb-*.log"
echo -e "\nService management:"
echo -e "  - sudo systemctl restart uwsgi         # Restart application server"
echo -e "  - sudo systemctl restart nginx         # Restart web server"
echo -e "  - sudo systemctl restart redis-server  # Restart Redis"
echo -e "  - sudo systemctl restart threatkb-celery  # Restart background tasks"
echo -e "\n${YELLOW}NOTE: Remember to secure your server with HTTPS for production use!${NC}"
