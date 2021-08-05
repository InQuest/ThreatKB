from setuptools import setup, find_packages

setup(
    name='threatkb',
    version='0.1.1',
    description='Knowledge base workflow management for Yara rules and C2 artifacts (IP, DNS, SSL)',

    url='https://github.com/InQuest/ThreatKB',

    author='Daniel Tijerina, Rohan Kotian, David Cuellar, Ryan Shipp, Pedram Amini',
    author_email='ryan.ship@inquest.net, pedram@inquest.net',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: InfoSec',

        'Licence :: ',

        'Programming Language :: Python :: 2.7',
    ],

    keywords='infosec yara c2 management',

    py_modules=['config'],
    packages=find_packages(exclude=['migrations', 'venv', 'contrib', 'docs', 'tests', 'build', 'dist', 'flask']),

    license='...',

    install_requires=[
        'alembic==0.9.4',
        'amqp==2.2.1',
        'app==0.0.1',
        'Babel==2.4.0',
        'bcrypt==3.1.3',
        'billiard==3.5.0.3',
        'blinker==1.4',
        'celery==4.1.0',
        'certifi==2017.11.5',
        'cffi==1.10.0',
        'chardet==3.0.4',
        'click==6.7',
        'decorator==4.0.11',
        'deepdiff==3.3.0',
        'dnspython==1.15.0',
        'Flask==1.0',
        'Flask-Autodoc==0.1.2',
        'Flask-Babel==0.8',
        'Flask-Bcrypt==0.7.1',
        'Flask-Login==0.4.0',
        'Flask-Mail==0.7.6',
        'Flask-Migrate==2.1.0',
        'Flask-OpenID==1.2.5',
        'Flask-Script==2.0.5',
        'Flask-SQLAlchemy==0.16',
        'Flask-WhooshAlchemy==0.54a0',
        'Flask-WTF==0.8.4',
        'flup==1.0.2',
        'geoip2==2.6.0',
        'idna==2.6',
        'ipaddr==2.1.11',
        'ipaddress==1.0.18',
        'ipwhois==1.0.0',
        'itsdangerous==0.24',
        'Jinja2==2.9.6',
        'jsonpickle==0.9.5',
        'kombu==4.1.0',
        'Mako==1.0.7',
        'MarkupSafe==1.0',
        'maxminddb==1.3.0',
        'migrate==0.3.8',
        'more-itertools==3.2.0',
        'MySQL-python==1.2.5',
        'ply==3.10',
        'pycparser==2.18',
        'pysqlite==2.8.3',
        'python-dateutil==2.6.1',
        'python-editor==1.0.3',
        'python-openid==2.2.5',
        'pytz==2017.2',
        'pyzipcode==1.0',
        'redis==2.10.6',
        'requests==2.20.0',
        'six==1.10.0',
        'speaklater==1.3',
        'SQLAlchemy==1.3.0',
        'sqlalchemy-migrate==0.7.2',
        'Tempita==0.5.2',
        'urllib3==1.25.6',
        'vine==1.1.4',
        'Werkzeug==0.15.3',
        'Whoosh==2.7.4',
        'WTForms==2.1',
        'yara-python==3.6.3'
    ],

    extra_require={
        'dev': [],
        'test': [],
    },

    include_package_data=True,
    package_data={
        'statics': ['app/static/*'],
        'config': ['config.py']
    },

    entry_points={
        'console_scripts': [
            'hunt = hunting.macro_hunter.cli:main',
            'vti_download = crawl.utils.vt_intelligence_downloader:main',
        ],
    },
)
