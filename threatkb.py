#!/bin/env python

import warnings

warnings.filterwarnings(action='ignore', module='.*crypto.*')

from docopt import docopt
from inspect import getdoc
from docopt import DocoptExit
import requests
import json
import sys
import os
import stat
import argparse
import fileinput
import logging
import tempfile
import urllib3
from logging.config import fileConfig
from termcolor import colored

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

API_KEY = None
SECRET_KEY = None
API_HOST = None
THREATKB_CLI = None
ENTITY_TYPES = {"yara_rule": 1, "c2dns": 2, "c2ip": 3, "task": 4}
ENTITY_MAP = {
    "c2ips": "c2ip",
    "c2dns": "c2dns",
    "tasks": "task",
    "yara_rules": "yara_rule"
}

FILTER_KEYS = None

urllib3.disable_warnings()

############################# configure logger  ################################

if os.getenv("THREATKB_DEBUG"):
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(processName)s - %(name)s - %(lineno)s - %(levelname)s - %(message)s')

LOG = logging.getLogger()

if os.path.exists("./logger.ini"):
    fileConfig("./logger.ini")


################################################################################

def get_docopt_help(docstring, *args, **kwargs):
    try:
        return docopt(docstring, *args, **kwargs)
    except DocoptExit:
        raise SystemExit(docstring)


class DocoptDispatcher:
    def __init__(self, command_cls, **options):
        self.command_cls = command_cls
        self.options = options

    def parse(self, argv):
        command_help = getdoc(self.command_cls) + "\n"
        options = get_docopt_help(command_help, argv, **self.options)
        command = options["COMMAND"]

        if command is None:
            raise SystemExit(command_help)

        if not hasattr(self.command_cls, command):
            print('Command "{%s}" not found \n' % (command))
            raise SystemExit(command_help)

        handler = getattr(self.command_cls, command)
        docstring = getdoc(handler)

        command_options = get_docopt_help(
            docstring, options["ARGS"], options_first=False
        )

        return handler, command_options


def create_tempfile(contents):
    fp = tempfile.TemporaryFile()
    fp.write(contents)
    fp.close()
    return fp.name


class ThreatKBCommand:
    """
    Usage:
        threatkb [COMMAND] [ARGS...] [OPTIONS]
        threatkb -h |--help
        threatkb --version

    Commands:
        c2ip        Interact with the c2ip api
        c2dns       Interact with the c2dns api
        yara_rule   Interact with the yara rules api
        task        Interact with the task api
        search      Global search
        import_api      Use the import api
        release     Pull release data from specific release
        configure   Configure the cli for api interaction
    """

    def __init__(self, std_in=None):
        self.std_in = std_in

    def configure(self, options):
        """
        Configure the cli to interact with a ThreatKB api endpoint

        Usage:
            configure

        """
        return ThreatKB.configure()

    def c2ip(self, options):
        """
        Interact with the c2ip api

        Usage:
            c2ip (get|g) (ID | --all)
            c2ip (delete|d) ID
            c2ip (update|u) ID (--file=FILE | [-])
            c2ip (create|c) (--file=FILE | [-])
            c2ip (comment|co) ID (--comment=COMMENT)

        Options:
            -f, --file FILE  Update or create json file
            -c, --comment COMMENT  Comment to be added to the c2ip

        Example FILE
            {
                "tags": ["abc"],
                "description": "A bad IP",
                "ip": "5.2.3.4",
                "state": "Imported",
                "references": "https://labs.inquest.net/dfi",
                "country": "United States",
                "asn": "Level 3 Communications Inc.",
                "expiration_timestamp": null
            }

        """
        params = {}
        print
        if options["get"] or options["g"]:
            action = "get"
            params["id"] = options["ID"] if "ID" in options else None

        elif options["delete"] or options["d"]:
            action = "delete"
            params["id"] = options["ID"]
        elif options["update"] or options["u"]:
            action = "update"
            params["id"] = options["ID"]
            if options["--file"]:
                params["file"] = options["--file"]
            else:
                params["file"] = create_tempfile(self.std_in)

        elif options["create"] or options["c"]:
            action = "create"
            if options["--file"]:
                params["file"] = options["--file"]
            else:
                params["file"] = create_tempfile(self.std_in)

        elif options["comment"] or options["c"]:
            action = "comment"
            params["id"] = options["ID"]
            params["comment"] = options["--comment"]

        try:
            return ThreatKB().c2ip(action, params)
        except Exception as e:
            LOG.error(e)

    def c2dns(self, options):
        """
        Interact with the c2dns api

        Usage:
            c2dns (get|g) (ID | --ids=<ids>| --all)
            c2dns (delete|d) ID
            c2dns (update|u) ID (--file=FILE | [-])
            c2dns (create|c) (--file=FILE | [-])
            c2dns (comment|co) ID (--comment=COMMENT)

        Options:
            -f, --file FILE  Update or create json file
            -c, --comment COMMENT  Comment to be added to the c2dns
            -i, --ids IDS  Comma-separated list of ids to fetch


        Example FILE:
            {
                "tags": ["abc"],
                "description": "A bad DNS",
                "domain_name": "foo1.com",
                "state": "Imported",
                "references": "https://labs.inquest.net/dfi"
            }

        """
        params = {}

        if options["get"] or options["g"]:
            action = "get"
            params["id"] = options["ID"] if "ID" in options else None

        elif options["delete"] or options["d"]:
            action = "delete"
            params["id"] = options["ID"]

        elif options["update"] or options["u"]:
            action = "update"
            params["id"] = options["ID"]
            if options["--file"]:
                params["file"] = options["--file"]
            else:
                params["file"] = create_tempfile(self.std_in)

        elif options["create"] or options["c"]:
            action = "create"
            if options["--file"]:
                params["file"] = options["--file"]
            else:
                params["file"] = create_tempfile(self.std_in)

        elif options["comment"] or options["c"]:
            action = "comment"
            params["id"] = options["ID"]
            params["comment"] = options["--comment"]

        try:
            return ThreatKB().c2dns(action, params)
        except Exception as e:
            LOG.exception(e)
            LOG.error(e)

    def task(self, options):
        """
        Interact with the task api

        Usage:
            task (get|g) (ID | --ids=<ids>| --all)
            task (delete|d) ID
            task (update|u) ID (--file=FILE | [-])
            task (create|c) (--file=FILE | [-])
            task (comment|co) ID (--comment=COMMENT)

        Options:
            -f, --file FILE  Update or create json file
            -c, --comment COMMENT  Comment to be added to the task
            -i, --ids IDS  Comma-separated list of ids to fetch

        Example FILE
            {
                "description": "task description",
                "title": "task title",
                "state": "Imported"
            }
        """
        params = {}
        print
        if options["get"] or options["g"]:
            action = "get"
            params["id"] = options["ID"] if "ID" in options else None

        elif options["delete"] or options["d"]:
            action = "delete"
            params["id"] = options["ID"]
        elif options["update"] or options["u"]:
            action = "update"
            params["id"] = options["ID"]
            if options["--file"]:
                params["file"] = options["--file"]
            else:
                params["file"] = create_tempfile(self.std_in)

        elif options["create"] or options["c"]:
            action = "create"
            if options["--file"]:
                params["file"] = options["--file"]
            else:
                params["file"] = create_tempfile(self.std_in)

        elif options["comment"] or options["c"]:
            action = "comment"
            params["id"] = options["ID"]
            params["comment"] = options["--comment"]

        try:
            return ThreatKB().task(action, params)
        except Exception as e:
            LOG.error(e)

    def yara_rule(self, options):
        """
        Interact with the yara_rule api

        Usage:
            yara_rule (get|g) (ID | --ids=<ids>| --all)
            yara_rule (delete|d) ID
            yara_rule (update|u) ID (--file=FILE | [-])
            yara_rule (create|c) (--file=FILE | [-])
            yara_rule (comment|co) ID (--comment=COMMENT)
            yara_rule (test|t) ID
            yara_rule (attach|a) ID (--file=FILE | [-])

        Options:
            -f, --file FILE  Update or create json file or a file to atach to the yara rule
            -c, --comment COMMENT  Comment to be added to the yara_rule
            -i, --ids IDS  Comma-separated list of ids to fetch

        Example FILE
            {
                "tags": ["abc"],
                "description": "yara danny rule description",
                "name": "yara rule name",
                "state": "Imported",
                "references": "https://labs.inquest.net/dfi",
                "category": "foo",
                "condition":"condition\n\ttrue",
                "strings": "strings:\n\t$c0 = /[0-9a-fA-F]{20}/ fullword ascii",
                "imports": "import \"pe\""
            }

        """
        params = {}

        if options["get"] or options["g"]:
            action = "get"
            params["id"] = options["ID"] if "ID" in options else None

        elif options["delete"] or options["d"]:
            action = "delete"
            params["id"] = options["ID"]
        elif options["update"] or options["u"]:
            action = "update"
            params["id"] = options["ID"]
            if options["--file"]:
                params["file"] = options["--file"]
            else:
                params["file"] = create_tempfile(self.std_in)

        elif options["create"] or options["c"]:
            action = "create"
            if options["--file"]:
                params["file"] = options["--file"]
            else:
                params["file"] = create_tempfile(self.std_in)

        elif options["comment"] or options["c"]:
            action = "comment"
            params["id"] = options["ID"]
            params["comment"] = options["--comment"]
        elif options["attach"] or options["a"]:
            action = "attach"
            params["id"] = options["ID"]

            if options["--file"]:
                params["file"] = options["--file"]
            else:
                params["file"] = create_tempfile(self.std_in)
        elif options["test"] or options["t"]:
            action = "test"
            params["id"] = options["ID"]

        try:
            return ThreatKB().yara_rule(action, params)
        except Exception as e:
            LOG.error(e)

    def search(self, options):
        """
        Global search

        Usage:
            search SEARCH_TEXT [--search-against=<against>] [--artifact-types=<artifact_types>]

        Options:
            -s, --search-against AGAINST    Search against: all, tag, state, category
            -t, --artifact-types ARTIFACT_TYPES    Comma-separated types to filter against: c2ips, c2dns, yara_rules, tasks
        """
        params = {}

        try:
            params["search_against"] = options["--search-against"]
            params["artifact_types"] = options["--artifact-types"]
            params["search_text"] = options["SEARCH_TEXT"]
            return ThreatKB().search(params)
        except Exception as e:
            LOG.exception(e)

    def release(self, options):
        """
        Get a release or all releases

        Usage:
            release (get|g) (ID | --all)
        """
        params = {}
        if options["get"] or options["g"]:
            action = "get"

        try:
            params["id"] = options["ID"] if "ID" in options else None
            return ThreatKB().release(action, params)
        except Exception as e:
            LOG.error(e)

    def import_api(self, options):
        """
        Use the import api

        Usage:
            import_api (--file=FILE | [-]) [--autocommit] [--shared-state=STATE] [--shared-reference=REFERENCE] [--shared-description=DESCRIPTION] [--exclude-ip] [--exclude-dns] [--exclude-yara-rule] [--metadata-mapping-file]

        Options:
            -f, --file FILE  File with import text
            -a, --autocommit     Automatically commit extracted artifacts
            -s, --shared-state STATE  Shared state for all imported artifacts
            -d, --shared-description DESCRIPTION  Shared description for all imported artifacts
            -r, --shared-reference REFERENCE  Shared reference for all imported artifacts
            -i, --exclude-ip  Exclude extracting IPs from import text [default: True].
            -n, --exclude-dns  Exclude extracting DNS from import text [default: True].
            -y, --exclude-yara-rule  Exclude extracting yara rules from import text [default: True].
            -m, --metadata-mapping-file  Provide a file that contains the metadata field mapping

        Example METADATA-MAPPING-FILE
            {
                "Author": "Author",
                "Category": "Category",
                "Confidence": "Confidence",
                "Creation_Date": "creation_date",
                "CVE": "CVE",
                "Description": "Description",
                "EventID": "EventID",
                "Exodus": "Exodus",
                "File_Type": "FileType",
                "Last_Revision_Date": "last_revision_date",
                "PII": "PII",
                "PP": "PP",
                "References": "References",
                "Revision": "Revision",
                "Severity": "Severity",
                "SubCategory1": "SubCategory1",
                "SubCategory2": "SubCategory2",
                "SubCategory3": "SubCategory3"
            }

        Example import text file
        "
            https://foo.bar.com

            1.1.1.1

            rule Big_Numbers0
            {
                meta:
                    author = "_pusher_"
                    description = "Looks for big numbers 20:sized"
                    date = "2016-07"
                strings:
                    $c0 = /[0-9a-fA-F]{20}/ fullword ascii
                condition:
                    $c0
            }https://foo.bar.com

            1.1.1.1

            rule Big_Numbers0
            {
                meta:
                    author = "_pusher_"
                    description = "Looks for big numbers 20:sized"
                    date = "2016-07"
                strings:
                    $c0 = /[0-9a-fA-F]{20}/ fullword ascii
                condition:
                    $c0
            }
        "
        """
        params = {}

        try:
            params["autocommit"] = options["--autocommit"]
            params["shared_state"] = options["--shared-state"]
            params["shared_description"] = options["--shared-description"]
            params["shared_reference"] = options["--shared-reference"]
            params["extract_ip"] = not options["--exclude-ip"]
            params["extract_dns"] = not options["--exclude-dns"]
            params["extract_signature"] = not options["--exclude-yara-rule"]
            params["metadata_field_mapping"] = "{}" if not options["--metadata-mapping-file"] else json.loads(
                open(options["metadata-mapping-file"], "r").read())
            if options["--file"]:
                params["import_text"] = open(options["--file"], "r").read()
            else:
                params["import_text"] = self.std_in

            return ThreatKB().import_api(params)
        except Exception as e:
            LOG.exception(e)


############################# transport class  ################################

class ThreatKBTransport:
    def __init__(self, host, token, secret_key, filter_on_keys=[], base_uri='ThreatKB/', use_https=True, log=LOG):
        self.host = host.lower().replace("http://", "").replace("https://", "")
        self.host = self.host if not self.host.endswith("/") else self.host.rstrip("/")
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
        LOG.debug(
            "method: %s - uri: %s - uri_params: %s - body: %s - files: %s" % (method, uri, uri_params, body, files))

        uri_params["token"] = self.token
        uri_params["secret_key"] = self.secret_key
        url = "%s://%s%s%s" % ("https" if self.use_https else "http", self.host, self.base_uri, uri)
        # Try hitting the uri
        if files:
            response = self.session.request(method, url, params=uri_params, data=body, verify=False, files=files)
        else:
            response = self.session.request(method, url, params=uri_params, json=body, verify=False, headers=headers)

        if response.status_code == 401:
            raise Exception("Invalid authentication token and secret key.")

        return response

    def get(self, endpoint, id_=None, params={}):
        """If index is None, list all; else get one"""
        r = self._request('GET', endpoint + ('/' + str(id_) if id_ else ''), uri_params=params)
        return self.filter_output(r.content)

    def update(self, endpoint, id_, json_data):
        r = self._request('PUT', '/'.join([endpoint, id_]), body=json_data)
        return r.content

    def delete(self, endpoint, id_):
        """True if '200 OK' else False"""
        return "SUCCESS" if self._request('DELETE', '/'.join([endpoint, id_])).status_code == 204 else "FAILED"

    def create(self, endpoint, json_data={}, files={}):
        if files:
            r = self._request('POST', endpoint, files=files, uri_params=json_data)
        else:
            r = self._request('POST', endpoint, body=json_data)
        if r.status_code == 412:
            return None
        return r.content


################################################################################

class ThreatKB:
    CREDENTIALS_FILE = os.path.expanduser('~/.threatkb/credentials')

    def __init__(self, **kwargs):
        self.credentials = ThreatKB.load_credentials()
        if not self.credentials:
            raise Exception("You must configure threatkb cli first.")
        if self.credentials["host"].startswith(("http://")):
            kwargs.update({"use_https": False})
        kwargs.update(self.credentials)
        self.threatkb_transport = ThreatKBTransport(**kwargs)

    @classmethod
    def load_credentials(cls):
        config = ConfigParser.ConfigParser()
        try:
            config.read(cls.CREDENTIALS_FILE)
            API_TOKEN = config.get("default", "token") or config.get("default", "secret_key")
            API_SECRET_KEY = config.get("default", "secret_key")
            API_HOST = config.get("default", "host") or config.get("default", "api_host")
            if not API_HOST.endswith("/"):
                API_HOST = "%s/" % (API_HOST)

            return {"token": API_TOKEN, "secret_key": API_SECRET_KEY, "host": API_HOST}
        except:
            pass

        return None

    @classmethod
    def configure(cls):
        credentials = cls.load_credentials()

        try:
            os.makedirs(os.path.dirname(cls.CREDENTIALS_FILE))
        except:
            pass

        print "Token [%s]: " % (
            "%s%s" % ("*" * 10, credentials["token"][-4:]) if credentials and "token" in credentials else "*" * 14),
        TOKEN = sys.stdin.readline().strip()
        print "Secret Key [%s]: " % ("%s%s" % (
        "*" * 10, credentials["secret_key"][-4:]) if credentials and "secret_key" in credentials else "*" * 14),
        SECRET_KEY = sys.stdin.readline().strip()
        print "API Host [%s]: " % ("%s" % (credentials["host"]) if credentials and "host" in credentials else "*" * 14),
        HOST = sys.stdin.readline().strip()

        config = ConfigParser.ConfigParser()
        config.readfp(StringIO('[default]'))
        config.set('default', 'token', TOKEN)
        config.set('default', 'secret_key', SECRET_KEY)
        config.set('default', 'host', HOST)
        with open(cls.CREDENTIALS_FILE, "w+") as configfile:
            config.write(configfile)

        os.chmod(cls.CREDENTIALS_FILE, stat.S_IRUSR | stat.S_IWUSR)
        return "Done"

    def _do_common_action(self, action, params, endpoint):
        global ENTITY_MAP

        if action.lower() == "get":
            return self.threatkb_transport.get(endpoint=endpoint, id_=params["id"])
        elif action.lower() == "update":
            return self.threatkb_transport.update(endpoint=endpoint, id_=params["id"],
                                                  json_data=json.loads(open(params["file"]).read()))
        elif action.lower() == "delete":
            return self.threatkb_transport.delete(endpoint=endpoint, id_=params["id"])
        elif action.lower() == "create":
            return self.threatkb_transport.create(endpoint=endpoint, json_data=json.loads(open(params["file"]).read()))
        elif action.lower() == "comment":
            comment = {"comment": params["comment"], "entity_type": ENTITY_TYPES.get(ENTITY_MAP[endpoint]),
                       "entity_id": params["id"]}
            return self.threatkb_transport.create(endpoint="comments", json_data=json.dumps(comment))

        raise Exception("Unsupport action '%s'" % (action))

    def c2ip(self, action, params):
        return self._do_common_action(action, params, endpoint="c2ips")

    def c2dns(self, action, params):
        return self._do_common_action(action, params, endpoint="c2dns")

    def task(self, action, params):
        return self._do_common_action(action, params, endpoint="tasks")

    def yara_rule(self, action, params):
        global ENTITY_MAP

        if action in ["get", "create", "update", "delete", "comment"]:
            return self._do_common_action(action, params, "yara_rules")
        elif action == "attach":
            json_data = {"entity_type": ENTITY_TYPES.get(ENTITY_MAP["yara_rules"]), "entity_id": params["id"]}
            file = {"file": open(params["file"], 'rb')}
            return self.threatkb_transport.create("file_upload", files=file, json_data=json_data)
        elif action == "test":
            return self.threatkb_transport.create("tests/create/%s" % (params["id"]))

    def release(self, action, params):
        return self._do_common_action(action, params, endpoint="releases")

    def search(self, params):
        mapping = {
            "c2ip": "ip",
            "c2ips": "ip",
            "ip": "ip",
            "ips": "ip",
            "c2dns": "dns",
            "dns": "dns",
            "signature": "signature",
            "yara_rule": "signature",
            "yara_rules": "signature",
            "task": "task"
        }
        uri_params = {}
        if not params["search_against"]:
            uri_params["all"] = params["search_text"]
        else:
            search_against = params["search_against"]
            uri_params[search_against] = params["search_text"]

        if params["artifact_types"]:
            uri_params["artifact_type"] = ",".join([mapping[entry] for entry in params["artifact_types"].split(",")])

        return self.threatkb_transport.get("search", params=uri_params)

    def import_api(self, params):
        default_mapping = {
            "Author": "Author",
            "Category": "Category",
            "Confidence": "Confidence",
            "Creation_Date": "creation_date",
            "CVE": "CVE",
            "Description": "Description",
            "EventID": "EventID",
            "Exodus": "Exodus",
            "File_Type": "FileType",
            "Last_Revision_Date": "last_revision_date",
            "PII": "PII",
            "PP": "PP",
            "References": "References",
            "Revision": "Revision",
            "Severity": "Severity",
            "SubCategory1": "SubCategory1",
            "SubCategory2": "SubCategory2",
            "SubCategory3": "SubCategory3"
        }

        if params["metadata_field_mapping"] in [False, "{}", {}]:
            params["metadata_field_mapping"] = json.dumps(default_mapping)

        return self.threatkb_transport.create("import", json_data=params)


def get_version_info():
    return "threatkb version 1.0"


def main(std_in=None):
    dispatcher = DocoptDispatcher(
        ThreatKBCommand, version=get_version_info(), options_first=True
    )
    handler, options = dispatcher.parse(sys.argv[1:])
    return handler(ThreatKBCommand(std_in), options)


if __name__ == "__main__":
    try:
        std_in = "".join(sys.stdin.readlines()) if not sys.stdin.isatty() else None
        result = main(std_in)
        if "Trace" in result:
            LOG.error("Server side error")
            LOG.error(result.replace("<BR>", "\n").replace("\\n", "\n").replace("&nbsp;", " "))
        else:
            print result
    except Exception, e:
        LOG.error("Exception when calling main")
        LOG.exception(e)
