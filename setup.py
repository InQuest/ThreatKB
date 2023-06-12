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
        'alembic==1.7.7',
        'amqp==5.1.1',
        'app==0.0.1',
        'Babel==2.10.1',
        'bcrypt==3.2.0',
        'billiard==3.6.4.0',
        'blinker==1.4',
        'celery==5.2.6',
        'certifi==2022.12.7',
        'cffi==1.15.0',
        'chardet==4.0.0',
        'click==8.1.2',
        'decorator==5.1.1',
        'deepdiff==5.8.0',
        'dnspython==2.0.0',
        'Flask==2.3.2',
        'Flask-Autodoc==0.1.2',
        'Flask-Babel==2.0.0',
        'Flask-Bcrypt==1.0.1',
        'Flask-Login==0.5.0',
        'Flask-Mail==0.9.1',
        'Flask-Migrate==2.6.0',
        'Flask-OpenID==1.3.0',
        'Flask-Script==2.0.6',
        'Flask-SQLAlchemy==2.5.1',
        'Flask-WhooshAlchemy==0.56',
        'Flask-WTF==1.0.1',
        'flup==1.0.3',
        'geoip2==4.5.0',
        'idna==3.3',
        'ipaddr==2.2.0',
        'ipaddress==1.0.23',
        'ipwhois==1.2.0',
        'itsdangerous==1.1.0',
        'Jinja2==2.11.3',
        'jsonpickle==2.1.0',
        'kombu==5.2.4',
        'Mako==1.2.2',
        'MarkupSafe==1.1.0',
        'maxminddb==2.2.0',
        'migrate==0.3.8',
        'more-itertools==8.12.0',
        'ply==3.11',
        'pycparser==2.21',
        'python-dateutil==2.8.2',
        'python-editor==1.0.4',
        'python-openid==2.2.5',
        'pytz==2022.1',
        'pyzipcode==3.0.1',
        'redis==4.2.2',
        'requests==2.31.0',
        'six==1.16.0',
        'speaklater==1.3',
        'SQLAlchemy==1.4.36',
        'sqlalchemy-migrate==0.13.0',
        'Tempita==0.5.2',
        'urllib3==1.26.9',
        'vine==5.0.0',
        'Werkzeug==0.15.5',
        'Whoosh==2.7.4',
        'WTForms==3.0.1',
        'yara-python==4.2.0'
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
