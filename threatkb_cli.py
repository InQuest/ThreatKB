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
from StringIO import StringIO

CREDENTIALS_FILE = os.path.expanduser('~/.threatkb/credentials')
API_KEY = None
SECRET_KEY = None


class ThreatKB:

    def __init__(self, host, token, secret_key, base_uri='ThreatKB/', use_https=True):
        self.host = host
        self.token = token
        self.secret_key = secret_key
        self.base_uri = base_uri
        self.use_https = use_https
        self.session = requests.Session()


    def _request(self, method, uri, uri_params={}, body=None):
        uri_params["token"] = self.token
        uri_params["secret_key"] = self.secret_key
        url = "%s://%s/%s/%s" % ("https" if self.use_https else "http", self.host, self.base_uri, uri)

        # Try hitting the uri
        response = self.session.request(method, url, params=uri_params, data=body, verify=False)
        if response.status_code == 401:
            raise Exception("Invalid authentication token and secret key.")

        return response

    def get(self, model, index=None):
        """If index is None, list all; else get one"""
        r = self._request('GET', model + ('/' + index if index else ''))
        return json.loads(r.content)

    def update(self, model, index, json_data):
        r = self._request('PUT', '/'.join(model, index), json_data)
        return json.loads(r.content)

    def delete(self, model, index):
        """True if '200 OK' else False"""
        return self._request('DELETE', '/'.join(model, index)).status_code == 200

    def create(self, model, json_data):
        r = self._request('POST', model, json_data)
        if r.status_code == 412:
            return None
        return json.loads(r.content)


def initialize():
    global API_KEY, SECRET_KEY

    config = ConfigParser.ConfigParser()
    try:
        config.read(CREDENTIALS_FILE)
        API_TOKEN = config.get("default", "token")
        API_SECRET_KEY = config.get("default", "secret_key")
    except:
        raise Exception("Error. Run 'python %s configure' first." % (sys.argv[0]))


def configure():
    global API_KEY, SECRET_KEY

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

    config = ConfigParser.ConfigParser()
    config.readfp(StringIO('[default]'))
    config.set('default', 'token', API_KEY)
    config.set('default', 'secret_key', SECRET_KEY)
    with open(CREDENTIALS_FILE, "wb") as configfile:
        config.write(configfile)


def attach(params):
    pass


def comment(params):
    pass


def release(params):
    pass


def main():
    action = sys.argv[1].lower()
    params = sys.argv[2:] if len(sys.argv) > 2 else None

    if action == "configure":
        configure()
    elif action == "attach":
        initialize()
        attach(params)
    elif action == "comments":
        initialize()
        comment(params)
    elif action == "release":
        initialize()
        release(params)


if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        sys.stderr.write(e.message + "\n")
        sys.exit(1)
