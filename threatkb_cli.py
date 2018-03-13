"""Client class.
Usage:
    import threatkb
    api = threatkb.ThreatKB('http://127.0.0.1:9000', 'user@email.tld', 'password')
    api.create('c2dns', {'domain_name': 'example.com', ... })
    dns = api.get('c2dns')
"""
import requests
import json
import sys
import re
import os
import ConfigParser
import stat
import traceback
import logging
from StringIO import StringIO

CREDENTIALS_FILE = os.path.expanduser('~/.threatkb/credentials')
API_KEY = None
SECRET_KEY = None
API_HOST = None
THREATKB_CLI = None
ENTITY_TYPES = {"yara_rule": 1, "c2dns": 2, "c2ip": 3, "task": 4}

if os.getenv("THREATKB_DEBUG"):
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(processName)s - %(name)s - %(lineno)s - %(levelname)s - %(message)s')

LOG = logging.getLogger()

class ThreatKB:
    def __init__(self, host, token, secret_key, base_uri='ThreatKB/', use_https=True, log=LOG):
        self.host = host.lower().replace("http://", "").replace("https://", "")
        self.token = token
        self.secret_key = secret_key
        self.base_uri = base_uri
        self.use_https = use_https
        self.log = log
        self.session = requests.Session()

    def _request(self, method, uri, uri_params={}, body=None, files={},
                 headers={"Content-Type": "application/json;charset=UTF-8"}):
        uri_params["token"] = self.token
        uri_params["secret_key"] = self.secret_key
        url = "%s://%s%s%s" % ("https" if self.use_https else "http", self.host, self.base_uri, uri)

        self.log.debug("Sending %s API request to: %s" % (method, url))
        # Try hitting the uri
        if files:
            response = self.session.request(method, url, params=uri_params, data=body, verify=False, files=files)
        else:
            response = self.session.request(method, url, params=uri_params, data=body, verify=False, headers=headers)

        if response.status_code == 401:
            raise Exception("Invalid authentication token and secret key.")

        return response

    def get(self, endpoint, id_=None, params={}):
        """If index is None, list all; else get one"""
        r = self._request('GET', endpoint + ('/' + str(id_) if id_ else ''), uri_params=params)
        return r.content

    def update(self, endpoint, id_, json_data):
        r = self._request('PUT', '/'.join(endpoint, id_), json_data)
        return r.content

    def delete(self, endpoint, id_):
        """True if '200 OK' else False"""
        return self._request('DELETE', '/'.join(endpoint, id_)).status_code == 200

    def create(self, endpoint, json_data={}, files={}):
        if files:
            r = self._request('POST', endpoint, files=files)
        else:
            r = self._request('POST', endpoint, body=json_data)
        if r.status_code == 412:
            return None
        return r.content


def initialize():
    global API_KEY, SECRET_KEY, API_HOST, THREATKB_CLI

    config = ConfigParser.ConfigParser()
    try:
        config.read(CREDENTIALS_FILE)
        API_TOKEN = config.get("default", "token")
        API_SECRET_KEY = config.get("default", "secret_key")
        API_HOST = config.get("default", "api_host")
        if not API_HOST.endswith("/"):
            API_HOST = "%s/" % (API_HOST)
    except:
        raise Exception("Error. Run 'python %s configure' first." % (sys.argv[0]))

    THREATKB_CLI = ThreatKB(host=API_HOST, token=API_TOKEN, secret_key=API_SECRET_KEY,
                            use_https=False if API_HOST.startswith("http://") else True)


def configure():
    global API_KEY, SECRET_KEY, API_HOST

    try:
        initialize()
    except Exception, e:
        pass

    try:
        os.makedirs(os.path.dirname(CREDENTIALS_FILE))
    except:
        pass

    API_KEY = raw_input("Token [%s]: " % ("%s%s" % ("*"*(len(API_KEY)-3), API_KEY[-3:]) if API_KEY else "*"*10))
    SECRET_KEY = raw_input("Secret Key [%s]: " % ("%s%s" % ("*"*(len(SECRET_KEY)-3), SECRET_KEY[-3:]) if SECRET_KEY else "*"*10))
    API_HOST = raw_input(
        "API Host [%s]: " % ("%s%s" % ("*" * (len(API_HOST) - 3), API_HOST[-3:]) if API_HOST else "*" * 10))

    config = ConfigParser.ConfigParser()
    config.readfp(StringIO('[default]'))
    config.set('default', 'token', API_KEY)
    config.set('default', 'secret_key', SECRET_KEY)
    config.set('default', 'api_host', API_HOST)
    with open(CREDENTIALS_FILE, "wb") as configfile:
        config.write(configfile)

    os.chmod(CREDENTIALS_FILE, stat.S_IRUSR | stat.S_IWUSR)


def attach(params):
    global THREATKB_CLI

    try:
        artifact, artifact_id, file = params[2:]
    except Exception, e:
        help(extra_text="""%s attach <artifact> <artifact_id> <file>
        
        artifact: yara_rule, c2dns, c2ip, task
        artifact_id: artifact id as an integer
        file: the file to attach to the entity""" % (params[0]), params=params)

    print THREATKB_CLI.create("file_upload",
                              files={"entity_type": artifact, "entity_id": artifact_id, "file": open(file, 'rb')})


def comment(params):
    global THREATKB_CLI, ENTITY_TYPES

    try:
        artifact, artifact_id, comment = params[2:]
    except Exception, e:
        help(extra_text="""%s comment <artifact> <artifact_id> <comment>
        
        artifact: yara_rule, c2dns, c2ip, task
        artifact_id: artifact id as an integer
        comment: the comment to add to the artifact""" % (params[0]), params=params)

    print THREATKB_CLI.create("comments", json.dumps(
        {"comment": comment, "entity_type": ENTITY_TYPES.get(artifact), "entity_id": artifact_id}))


def release(params):
    global THREATKB_CLI

    try:
        release_id = params[2]
    except Exception, e:
        release_id = None

    print THREATKB_CLI.get("releases", release_id, {"full": 1})


def search(params):
    global THREATKB_CLI

    try:
        filter_, filter_text = params[2:]
    except Exception, e:
        help(extra_text="""%s search <filter> <filter_text>
        
        filter: tag, state, description, category
        filter_text: text to filter on""" % (params[0]), params=params)

    print THREATKB_CLI.get("search", params={filter_: filter_text})


def help(params, extra_text="", exit=True):
    sys.stderr.write("""
    %s <command> 
    
    Commands:
      configure: Configure the cli api
      attach: attach a file to an artifact
      comments: comment on an artifact
      release: pull release data from a specific release
      search: search the database
    
    %s
    """ % (params[0], extra_text))
    if exit:
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        help(sys.argv)

    action = sys.argv[1].lower()
    params = sys.argv

    if action == "configure":
        configure()
    elif action == "attach":
        initialize()
        attach(params)
    elif action == "comment":
        initialize()
        comment(params)
    elif action == "release":
        initialize()
        release(params)
    elif action == "search":
        initialize()
        search(params)
    else:
        help(sys.argv)


if __name__ == "__main__":
    main()
