<p align="center">
  <img src="https://raw.githubusercontent.com/InQuest/ThreatKB/rc/.github/wiki/inquest_logo.svg" />
</p>

### NOTE: THIS REPO IS IN AN ALPHA STATE

ThreatKB is a knowledge base workflow management dashboard for YARA rules and C2 artifacts. Rules are categorized and used to denote intent, severity, and confidence in accumulated artifacts.

## Quick Start

ThreatKB can be deployed in multiple ways depending on your environment and requirements:

- **🐳 [Docker Compose](#docker-installation)** (Recommended) - Complete stack with all dependencies
- **🖥️ [Native Installation](#native-installation)** - Direct installation on Ubuntu/Debian systems
- **🐧 [Other Linux Distributions](#other-linux-distributions)** - Manual installation on CentOS, RHEL, etc.

## Docker Installation

### Prerequisites
- Docker and Docker Compose installed
- At least 2GB RAM available
- Ports 80, 3306, 5000, 6379 available

### Quick Deploy

```bash
# Clone the repository
git clone https://github.com/InQuest/ThreatKB.git
cd ThreatKB

# Build the Docker image
docker build -t threatkb:latest .

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Services Included
- **ThreatKB Application** (Port 5000)
- **Nginx Reverse Proxy** (Port 80)
- **MySQL Database** (Port 3306)
- **Redis Cache** (Port 6379)
- **Celery Worker** (Background tasks)

### Default Credentials
- **Username**: `admin@inquest.net`
- **Password**: `b5vXcqzUtn4suyS`

⚠️ **Change default passwords in production!**

### Customization

Edit `docker-compose.yml` to customize:
- Database passwords
- Admin credentials
- Port mappings
- Volume mounts

## Native Installation

### Supported Systems
- Ubuntu 20.04+ (Primary support)
- Debian 10+ (Primary support)
- Other Linux distributions (see [Other Linux Distributions](#other-linux-distributions))

### Prerequisites
- Root or sudo access
- Internet connection for package downloads
- At least 2GB RAM and 10GB disk space

### Automated Installation

```bash
# Clone the repository
git clone https://github.com/InQuest/ThreatKB.git
cd ThreatKB

# Run the deployment script
sudo ./deploy-native.sh
```

#### Installation Options

The script will prompt you to choose between:

**Option 1: Local MySQL Installation (Recommended)**
- Automatically installs and configures MySQL server
- Creates secure database and user with generated passwords
- Saves credentials to `/opt/threatkb/.mysql_credentials`
- Perfect for new deployments and development

**Option 2: Remote MySQL Connection**
- Connects to existing MySQL server
- Prompts for database connection details
- Ideal for production environments with dedicated database servers

#### What the Script Does:
1. **System Setup**: Installs Python, Node.js, Nginx, uWSGI, Redis
2. **MySQL Setup**: Either installs MySQL locally OR configures remote connection
3. **Database**: Creates database schema and default admin user
4. **Application**: Sets up ThreatKB with secure configuration
5. **Web Server**: Configures Nginx reverse proxy
6. **Services**: Starts and enables all required services
7. **Background Tasks**: Configures Celery worker for async operations

### Manual Configuration

After installation, you can customize:

- **Database settings**: `/opt/threatkb/app/config.py`
- **Nginx configuration**: `/etc/nginx/sites-available/threatkb`
- **uWSGI settings**: `/etc/uwsgi/apps-available/threatkb.ini`
- **Application logs**: `/var/log/uwsgi/threatkb.log`

## Other Linux Distributions

### CentOS / RHEL / Rocky Linux

```bash
# Install EPEL repository
sudo dnf install epel-release -y

# Install dependencies
sudo dnf groupinstall "Development Tools" -y
sudo dnf install python3 python3-devel python3-pip nodejs npm mysql-server mysql-devel \
                 nginx uwsgi uwsgi-plugin-python3 redis git libffi-devel openssl-devel -y

# Start services
sudo systemctl enable --now mysqld redis nginx

# Clone and adapt the deployment script
git clone https://github.com/InQuest/ThreatKB.git
cd ThreatKB

# Edit deploy-native.sh to use 'dnf' instead of 'apt-get'
# Then run the modified script
sudo ./deploy-native.sh
```

### Arch Linux

```bash
# Install dependencies
sudo pacman -S python python-pip nodejs npm mysql nginx uwsgi uwsgi-plugin-python \
               redis git base-devel libffi openssl

# Enable services
sudo systemctl enable --now mysqld redis nginx

# Follow native installation steps
git clone https://github.com/InQuest/ThreatKB.git
cd ThreatKB
sudo ./deploy-native.sh
```

### Alpine Linux

```bash
# Install dependencies
sudo apk add python3 python3-dev py3-pip nodejs npm mysql mysql-dev mysql-client \
            nginx uwsgi uwsgi-python3 redis git build-base libffi-dev openssl-dev

# Start services
sudo rc-service mysql start
sudo rc-service redis start
sudo rc-service nginx start

# Add to startup
sudo rc-update add mysql default
sudo rc-update add redis default
sudo rc-update add nginx default

# Follow native installation
git clone https://github.com/InQuest/ThreatKB.git
cd ThreatKB
sudo ./deploy-native.sh
```

### Generic Linux Installation

For other distributions, ensure these dependencies are installed:

**System Packages:**
- Python 3.8+ with development headers
- Node.js 14+ and npm
- MySQL 8.0+ server and client
- Nginx web server
- uWSGI with Python plugin
- Redis server
- Git, build tools, libffi, OpenSSL development headers

**Python Packages:**
- All packages from `requirements.txt`
- Virtual environment support

**Services:**
- MySQL, Redis, Nginx should be running and enabled

Then adapt the `deploy-native.sh` script for your package manager.

## Post-Installation

### Access ThreatKB
- **URL**: `http://your-server-ip/` or `http://localhost/`
- **Default Login**: `admin@inquest.net` / `b5vXcqzUtn4suyS`

### Service Management

```bash
# Check all service status
sudo systemctl status uwsgi nginx redis

# For local MySQL installations, also check:
sudo systemctl status mysql

# Restart individual services
sudo systemctl restart uwsgi          # Application server
sudo systemctl restart nginx          # Web server
sudo systemctl restart redis-server   # Cache
sudo systemctl restart mysql          # Database (local only)

# View service logs
sudo tail -f /var/log/uwsgi/threatkb.log     # Application logs
sudo tail -f /var/log/nginx/threatkb-error.log  # Web server errors
sudo journalctl -u uwsgi -f                 # Real-time app logs
sudo journalctl -u mysql -f                 # MySQL logs (local only)
```

### Troubleshooting

**Application not loading:**
```bash
# Check uWSGI logs
sudo tail -f /var/log/uwsgi/threatkb.log

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Verify services are running
sudo systemctl status uwsgi nginx mysql
```

**Database connection issues:**

*For Local MySQL:*
```bash
# Check MySQL service status
sudo systemctl status mysql

# Test local database connection
mysql -u threatkb -p threatkb

# View saved credentials
sudo cat /opt/threatkb/.mysql_credentials

# Restart MySQL if needed
sudo systemctl restart mysql
```

*For Remote MySQL:*
```bash
# Test remote connection
mysql -h your-mysql-host -P 3306 -u your-user -p your-database

# Check network connectivity
telnet your-mysql-host 3306

# Verify firewall rules on remote server
# Ensure MySQL user has proper host permissions
```

*General Database Troubleshooting:*
```bash
# Check database configuration
grep -A 10 "SQLALCHEMY_DATABASE_URI" /opt/threatkb/app/config.py

# Test database schema
cd /opt/threatkb && source env/bin/activate
export FLASK_APP=app
flask db current  # Check current migration version
```

**Permission issues:**
```bash
# Fix file permissions
sudo chown -R www-data:www-data /opt/threatkb
sudo chmod +x /opt/threatkb/wsgi.py
```

## Optional: Datadog APM Integration

For production monitoring, you can add Datadog APM integration:

```bash
# After ThreatKB is installed and working
cd /path/to/datadog-apm-integration
sudo ./install-ddtrace-apm.sh
```

This adds performance monitoring without modifying core ThreatKB files. See the [APM Integration README](../datadog-apm-integration/README.md) for details.

## Development

### Local Development

```bash
# Clone repository
git clone https://github.com/InQuest/ThreatKB.git
cd ThreatKB

# Create virtual environment
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
npm install -g bower
bower install

# Set up database (MySQL must be running)
export FLASK_APP=app
flask db upgrade

# Run development server
python run.py --debug
```

### Development with Docker

```bash
# Use development compose file
docker-compose -f docker-compose.dev.yml up -d
```

## Documentation

* [Wiki Home](https://github.com/InQuest/ThreatKB/wiki)
* [Getting Started Guide](https://github.com/InQuest/ThreatKB/wiki/Getting-Started)
* [Database Structure](https://github.com/InQuest/ThreatKB/wiki/Database-Structure)
* [API Documentation](https://github.com/InQuest/ThreatKB/wiki/Documentation)
* [FAQ](https://github.com/InQuest/ThreatKB/wiki/Frequently-Asked-Questions)

## Thank You
ThreatKB utilizes Plyara to parse YARA rules into Python dictionaries. A huge thank you to the Plyara team! Links to the project are below:

- [Plyara](https://github.com/plyara/plyara) ([LICENSE](https://github.com/plyara/plyara/blob/master/LICENSE))

When a release is created, the system first pulls all signatures that are in the release state. Then, it gathers all signatures that are in the staging state and checks their revision history for the most recently released revision that is in the release state. If it finds it, it will include it in the release. If it does not find any previously released revisions, it will skip the signature.
