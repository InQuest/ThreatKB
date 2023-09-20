import os
from setuptools import setup, find_packages

requirements = open(os.path.join(os.path.dirname(__file__), "requirements.txt")).read().strip().split('\n')

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
    license='GPL-2.0',
    install_requires=requirements,
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
