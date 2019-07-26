#!/bin/env python
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
import os
import stat
import argparse
import logging

# python2/3 compatability hacks.
try:
    import ConfigParser
except:
    from configparser import ConfigParser

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

raw_input = input
    
CREDENTIALS_FILE = os.path.expanduser('~/.threatkb/credentials')
API_KEY = None
SECRET_KEY = None
API_HOST = None
THREATKB_CLI = None
ENTITY_TYPES = {"yara_rule": 1, "c2dns": 2, "c2ip": 3, "task": 4}
FILTER_KEYS = None

if os.getenv("THREATKB_DEBUG"):
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(processName)s - %(name)s - %(lineno)s - %(levelname)s - %(message)s')

LOG = logging.getLogger()


class ThreatKB:
    def __init__(self, host, token, secret_key, filter_on_keys=[], base_uri='/', use_https=True, log=LOG):
        self.host = host.lower().replace("http://", "").replace("https://", "")
        self.token = token
        self.secret_key = secret_key
        self.base_uri = base_uri
        self.use_https = use_https
        self.log = log
        self.filter_on_keys = filter_on_keys
        self.session = requests.Session()

        # ensure base URI is wrapped in slashes or, if not specified, is a slash.
        if self.base_uri:
            if not self.base_uri.startswith("/"):
                self.base_uri = "/" + self.base_uri
            if not self.base_uri.endswith("/"):
                self.base_uri = self.base_uri + "/"
        else:
            self.base_uri = "/"
        
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

    def filter_output(self, output):
        try:

            o = json.loads(output)
            if type(o) == dict:
                return dict(zip(self.filter_on_keys, [o[k] for k in self.filter_on_keys]))
            else:
                results = []
                for obj in o:
                    results.append(dict(zip(self.filter_on_keys, [obj[k] for k in self.filter_on_keys])))
                return results
                # return project(o, self.filter_on_keys)
        except Exception:
            return output

    def get(self, endpoint, id_=None, params={}):
        """If index is None, list all; else get one"""
        r = self._request('GET', endpoint + ('/' + str(id_) if id_ else ''), uri_params=params)
        return self.filter_output(r.content)

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
    global API_KEY, SECRET_KEY, API_HOST, THREATKB_CLI, FILTER_KEYS

    config = ConfigParser()
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
                            use_https=False if API_HOST.startswith("http://") else True,
                            filter_on_keys=FILTER_KEYS)


def configure():
    global API_KEY, SECRET_KEY, API_HOST

    try:
        initialize()
    except Exception:
        pass

    try:
        os.makedirs(os.path.dirname(CREDENTIALS_FILE))
    except:
        pass

    API_KEY = raw_input("Token [%s]: " % ("%s%s" % ("*" * (len(API_KEY) - 3), API_KEY[-3:]) if API_KEY else "*" * 10))
    SECRET_KEY = raw_input(
        "Secret Key [%s]: " % ("%s%s" % ("*" * (len(SECRET_KEY) - 3), SECRET_KEY[-3:]) if SECRET_KEY else "*" * 10))
    API_HOST = raw_input(
        "API Host [%s]: " % ("%s%s" % ("*" * (len(API_HOST) - 3), API_HOST[-3:]) if API_HOST else "*" * 10))

    config = ConfigParser()
    config.readfp(StringIO('[default]'))
    config.set('default', 'token', API_KEY)
    config.set('default', 'secret_key', SECRET_KEY)
    config.set('default', 'api_host', API_HOST)
    with open(CREDENTIALS_FILE, "w+") as configfile:
        config.write(configfile)

    os.chmod(CREDENTIALS_FILE, stat.S_IRUSR | stat.S_IWUSR)


def attach(params):
    global THREATKB_CLI

    try:
        artifact, artifact_id, file = params[1:]
    except Exception as e:
        help(extra_text="""%s attach <artifact> <artifact_id> <file>
        
        artifact: yara_rule, c2dns, c2ip, task
        artifact_id: artifact id as an integer
        file: the file to attach to the entity""" % (params[0]), params=params)

    print(THREATKB_CLI.create("file_upload",
                              files={"entity_type": artifact, "entity_id": artifact_id, "file": open(file, 'rb')}))


def comment(params):
    global THREATKB_CLI, ENTITY_TYPES

    try:
        artifact, artifact_id, comment = params[1:]
    except Exception as e:
        help(extra_text="""%s comment <artifact> <artifact_id> <comment>
        
        artifact: yara_rule, c2dns, c2ip, task
        artifact_id: artifact id as an integer
        comment: the comment to add to the artifact""" % (params[0]), params=params)

    print(THREATKB_CLI.create("comments", json.dumps(
        {"comment": comment, "entity_type": ENTITY_TYPES.get(artifact), "entity_id": artifact_id})))


def release(params):
    global THREATKB_CLI

    try:
        release_id = params[1]
    except Exception as e:
        release_id = None

    print(THREATKB_CLI.get("releases", release_id, {"short": 0}))


def search(params):
    global THREATKB_CLI

    try:
        filter_, filter_text = params[1:]
    except Exception as e:
        help(extra_text="""%s search <filter> <filter_text>
        
        filter: all, tag, state, category
        filter_text: text to filter on""" % (params[0]), params=params)

    print(THREATKB_CLI.get("search", params={filter_: filter_text}))


def help(params, extra_text="", exit=True):
    return """
    %s <options> <command> 
    
    Options:
      --filter-on-field: Object field to filter on. (EX: You only want the IDs of some search result)
    
    Commands:
      configure: Configure the cli api
      attach: attach a file to an artifact
      comments: comment on an artifact
      release: pull release data from a specific release
      search: search the database

    %s
    """ % (params[0], extra_text)


def main():
    global FILTER_KEYS

    if len(sys.argv) < 2:
        help(sys.argv)

    parser = argparse.ArgumentParser(
        description="threatkb_cli.py is a cli tool for interacting with the ThreatKB API.",
        usage=help(sys.argv)
    )

    # Define accepted arguments and metadata.
    parser.add_argument('--filter-on-keys',
                        action='store',
                        type=str,
                        default=None,
                        dest='filter_keys_only',
                        help=argparse.SUPPRESS)

    args, params = parser.parse_known_args()

    try:
        action = params[0]
    except:
        print(help(sys.argv))
        sys.exit(1)

    if args.filter_keys_only:
        FILTER_KEYS = [key.strip() for key in args.filter_keys_only.split(",")]

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
