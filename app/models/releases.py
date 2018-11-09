from app import db
from app.models import c2dns, c2ip, yara_rule, cfg_settings, cfg_states, metadata, users
from sqlalchemy import and_
from dateutil import parser
from datetime import datetime
import json
from sqlalchemy.event import listens_for
import StringIO
import zipfile
import zlib
import re

class Release(db.Model):
    __tablename__ = "releases"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), nullable=False)
    is_test_release = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    _release_data = db.Column(db.LargeBinary, nullable=False)
    num_signatures = db.Column(db.Integer)
    num_ips = db.Column(db.Integer)
    num_dns = db.Column(db.Integer)

    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==Release.created_user_id")

    @property
    def release_data(self):
        try:
            return zlib.decompress(self._release_data)
        except:
            return self._release_data

    @release_data.setter
    def release_data(self, value):
        self._release_data = zlib.compress(value, 8)

    @property
    def release_data_dict(self):
        return json.loads(self.release_data) if self.release_data else {}

    def to_small_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            is_test_release=self.is_test_release,
            date_created=self.date_created.isoformat(),
            created_user=self.created_user.to_dict(),
            num_signatures=self.num_signatures or 0,
            num_ips=self.num_ips or 0,
            num_dns=self.num_dns or 0
        )

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            is_test_release=self.is_test_release,
            release_data=self.release_data,
            date_created=self.date_created.isoformat(),
            created_user=self.created_user.to_dict(),
            num_signatures=len(self.release_data_dict["Signatures"]["Signatures"]) if self.release_data_dict.get(
                "Signatures", None) and self.release_data_dict["Signatures"].get("Signatures", None) else 0,
            num_ips=len(self.release_data_dict["IP"]["IP"]) if self.release_data_dict.get("IP", None) and
                                                               self.release_data_dict["IP"].get("IP", None) else 0,
            num_dns=len(self.release_data_dict["DNS"]["DNS"]) if self.release_data_dict.get("DNS", None) and
                                                                 self.release_data_dict["DNS"].get("DNS", None) else 0
        )

    def get_release_data(self):
        if self.release_data:
            return self.release_data

        release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
        staging_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_staging_state > 0).first()
        retired_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_retired_state > 0).first()

        if not release_state:
            raise Exception("You need to specify a production release state first.")

        if not staging_state:
            raise Exception("You need to specify a staging release state first.")

        if not retired_state:
            raise Exception("You need to specify a retired release state first.")

        dns = c2dns.C2dns.query.filter(c2dns.C2dns.state == release_state.state).all()
        ip = c2ip.C2ip.query.filter(c2ip.C2ip.state == release_state.state).all()
        yr = yara_rule.Yara_rule.query\
            .filter(and_(yara_rule.Yara_rule.state == release_state.state, yara_rule.Yara_rule.active > 0))\
            .all()

        metadata_cache = metadata.Metadata.get_metadata_cache()
        user_cache = users.KBUser.get_user_cache()

        release_data = {
            "Signatures": {"Signatures": {
            entity.to_release_dict(metadata_cache, user_cache)["id"]: entity.to_release_dict(metadata_cache, user_cache)
            for entity in yr},
                           "Added": [],
                           "Removed": [], "Modified": []},
            "DNS": {"DNS": {
            entity.to_release_dict(metadata_cache, user_cache)["id"]: entity.to_release_dict(metadata_cache, user_cache)
            for entity in dns}, "Added": [], "Removed": [],
                    "Modified": []},
            "IP": {"IP": {
            entity.to_release_dict(metadata_cache, user_cache)["id"]: entity.to_release_dict(metadata_cache, user_cache)
            for entity in ip}, "Added": [], "Removed": [],
                   "Modified": []}}

        # release_data = {
        #     "Signatures": {"Signatures": {entity.to_dict()["id"]: entity.to_dict() for entity in yr},
        #                    "Added": [],
        #                    "Removed": [], "Modified": []},
        #     "DNS": {"DNS": {entity.to_dict()["id"]: entity.to_dict() for entity in dns}, "Added": [], "Removed": [],
        #             "Modified": []},
        #     "IP": {"IP": {entity.to_dict()["id"]: entity.to_dict() for entity in ip}, "Added": [], "Removed": [],
        #            "Modified": []}}

        staging_yr = yara_rule.Yara_rule.query \
            .filter(and_(yara_rule.Yara_rule.state == staging_state.state, yara_rule.Yara_rule.active > 0)) \
            .all()

        for staging_yr_rule in staging_yr:
            staging_yr_rule_last_release_version = yara_rule.Yara_rule_history.query.filter(
                and_(yara_rule.Yara_rule_history.yara_rule_id == staging_yr_rule.id,
                     yara_rule.Yara_rule_history.state == release_state.state)).order_by(
                yara_rule.Yara_rule_history.date_created.desc()).limit(1).first()
            if staging_yr_rule_last_release_version:
                release_data["Signatures"]["Signatures"][
                    staging_yr_rule_last_release_version.yara_rule_id] = json.loads(
                    staging_yr_rule_last_release_version.rule_json)

        last_release = Release.query.filter(Release.is_test_release == 0).order_by(Release.id.desc()).first()

        if not last_release or not all(
            [artifact in last_release.release_data_dict for artifact in ["Signatures", "IP", "DNS"]]):
            release_data["Signatures"]["Added"] = [sig for id_, sig in
                                                   release_data["Signatures"]["Signatures"].iteritems()]
            release_data["IP"]["Added"] = [ip for id_, ip in release_data["IP"]["IP"].iteritems()]
            release_data["DNS"]["Added"] = [dns for id_, dns in release_data["DNS"]["DNS"].iteritems()]
            return json.dumps(release_data)

        last_release_date = last_release.date_created
        last_release = last_release.release_data_dict

        ##### SIGNATURES #######
        release_eventids = release_data["Signatures"]["Signatures"].keys()
        last_release_eventids = [long(release_id) for release_id in
                                 last_release["Signatures"]["Signatures"].keys()]

        try:
            for signature in release_data["Signatures"]["Signatures"].values():
                eventid = signature["id"]
                if not eventid in last_release_eventids:
                    release_data["Signatures"]["Added"].append(signature)
                else:
                    if not signature["last_revision_date"] or parser.parse(
                        signature["last_revision_date"]) > last_release_date:
                        release_data["Signatures"]["Modified"].append(signature)
                    del last_release["Signatures"]["Signatures"][str(eventid)]

            for signature in last_release["Signatures"]["Signatures"].values():
                release_data["Signatures"]["Removed"].append(signature)
        except Exception, e:
            raise Exception(e.message + "\nSignature: id=%s, description=%s" % (signature["id"], signature["name"]))

        ###### IPs ########
        release_ips = release_data["IP"]["IP"].keys()
        last_release_ips = [long(release_id) for release_id in last_release["IP"]["IP"].keys()]

        try:
            for ip in release_data["IP"]["IP"].values():
                ip_id = ip["id"]
                if not ip_id in last_release_ips:
                    release_data["IP"]["Added"].append(ip)
                else:
                    if parser.parse(ip["date_modified"]) > last_release_date:
                        release_data["IP"]["Modified"].append(ip)
                    del last_release["IP"]["IP"][str(ip_id)]

            for ip in last_release["IP"]["IP"].values():
                release_data["IP"]["Removed"].append(ip)
        except Exception, e:
            raise Exception(e.message + "\n IP: id=%s,ip=%s" % (ip["id"], ip["ip"]))

        ###### DNS #######
        release_dns = release_data["DNS"]["DNS"].keys()
        last_release_dns = [long(release_id) for release_id in last_release["DNS"]["DNS"].keys()]

        try:
            for dns in release_data["DNS"]["DNS"].values():
                dns_id = dns["id"]
                if not dns_id in last_release_dns:
                    release_data["DNS"]["Added"].append(dns)
                else:
                    if parser.parse(dns["date_modified"]) > last_release_date:
                        release_data["DNS"]["Modified"].append(dns)
                    del last_release["DNS"]["DNS"][str(dns_id)]

            for ip in last_release["DNS"]["DNS"].values():
                release_data["DNS"]["Removed"].append(ip)
        except Exception, e:
            raise Exception(e.message + "\n DNS: id=%s,domain_name=%s" % (dns["id"], dns["domain_name"]))

        return json.dumps(release_data)

    def generate_release_notes(self):
        prepend_text = cfg_settings.Cfg_settings.get_setting("RELEASE_PREPEND_TEXT")
        postpend_text = cfg_settings.Cfg_settings.get_setting("RELEASE_APPEND_TEXT")

        message = "%s\n\n" % (prepend_text) if prepend_text else ""
        message += "New Signatures\n%s\n" % ("-" * 10)
        message += "\n\n".join(["EventID: %s\nName: %s\nCategory: %s\nConfidence: %s\nSeverity: %s\nDescription: %s" % (
            entity.get("eventid", "eventid"),
            entity.get("name", "name"),
            entity.get("category", "category"),
            entity["metadata_values"].get("Confidence", {"value": "Confidence"})["value"],
            entity["metadata_values"].get("Severity", {"value": "Severity"})["value"],
            entity.get("description", "description"),
        ) for entity in self.release_data_dict["Signatures"]["Added"] if
                                type(entity) == dict]) if \
            len(self.release_data_dict["Signatures"]["Added"]) > 0 else "NA"
        message += "\n\nRemoved Signatures\n%s\n" % ("-" * 10)
        message += "\n\n".join(["EventID: %s\nName: %s\nCategory: %s" % (
            entity.get("eventid", "eventid"),
            entity.get("name", "name"),
            entity.get("category", "category")) for entity in self.release_data_dict["Signatures"]["Removed"] if
                                type(entity) == dict]) if \
            len(self.release_data_dict["Signatures"]["Removed"]) > 0 else "NA"
        message += "\n\nModified Signatures\n%s\n" % ("-" * 10)
        message += "\n\n".join(["EventID: %s\nName: %s\nCategory: %s\nConfidence: %s\nSeverity: %s\nDescription: %s" % (
            entity.get("eventid", "eventid"),
            entity.get("name", "name"),
            entity.get("category", "category"),
            entity["metadata_values"].get("Confidence", {"value": "Confidence"})["value"],
            entity["metadata_values"].get("Severity", {"value": "Severity"})["value"],
            entity.get("description", "description"),
        ) for entity in
                                self.release_data_dict["Signatures"]["Modified"] if type(entity) == dict]) if \
            len(self.release_data_dict["Signatures"]["Modified"]) > 0 else "NA"

        message += "\n\nFeed Content\n%s\n" % ("-" * 10)
        message += "C2 IPs Added: %s\n" % (len(self.release_data_dict["IP"]["Added"]))
        message += "C2 IPs Removed: %s\n" % (len(self.release_data_dict["IP"]["Removed"]))
        message += "C2 Domains Added: %s\n" % (len(self.release_data_dict["DNS"]["Added"]))
        message += "C2 Domains Removed: %s\n" % (len(self.release_data_dict["DNS"]["Removed"]))

        message += "\n\n%s" % (postpend_text) if postpend_text else ""

        stream = StringIO.StringIO()
        stream.write(message)
        return stream

    def generate_artifact_export(self):
        release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
        ip_text_filename = cfg_settings.Cfg_settings.query.filter_by(key="EXPORT_FILENAME_IP").first()
        ip_text_filename = ip_text_filename.value if ip_text_filename else "IPs.csv"
        dns_text_filename = cfg_settings.Cfg_settings.query.filter_by(key="EXPORT_FILENAME_DNS").first()
        dns_text_filename = dns_text_filename.value if dns_text_filename else "DNS.csv"
        signature_directory = cfg_settings.Cfg_settings.query.filter_by(key="EXPORT_DIRECTORY_SIGNATURE").first()
        signature_directory = signature_directory.value if signature_directory else "signatures"

        date_format = "%Y-%m-%d"

        if not release_state:
            raise Exception("You need to specify a production release state first.")

        combined_rules = {}
        for signature in sorted(self.release_data_dict["Signatures"]["Signatures"].values(),
                                key=lambda x: x["eventid"]):
            category = signature.get("category")
            if not signature["category"] in combined_rules:
                combined_rules[category] = []

            combined_rules[category].append(signature)

        ips = []
        for ip in self.release_data_dict["IP"]["IP"].values():
            output = "%s,%s" % (parser.parse(ip.get("date_created")).strftime(date_format), ip.get("ip"))
            if "description" in ip.keys():
                output += "," + (ip.get("description", None) or "")
            ips.append(output)

        ips.sort()

        dns = []
        for d in self.release_data_dict["DNS"]["DNS"].values():
            output = "%s,%s" % (parser.parse(d.get("date_created")).strftime(date_format), d.get("domain_name"))
            if "description" in d.keys():
                output += "," + (d.get("description", None) or "")
            dns.append(output)

        dns.sort()

        memzip = StringIO.StringIO()
        z = zipfile.ZipFile(memzip, mode="w", compression=zipfile.ZIP_DEFLATED)
        for category, rules in combined_rules.iteritems():
            imports = []
            for rule in rules:
                if rule.get("imports", None):
                    imports.extend(rule["imports"].split("\n"))
            imports = "\n".join(set(imports))
            rules_string = ""
            for signature in rules:
                try:
                    yara_string = yara_rule.Yara_rule.to_yara_rule_string(signature, include_imports=False)
                    rules_string += re.sub("[^\x00-\x7f]", "", yara_string) + "\n\n"
                except Exception, e:
                    raise Exception(e.message + "\nYaraRule: id=%s,name=%s" % (signature["id"], signature["name"]))

            rules = "%s\n\n%s" % (imports, rules_string)
            z.writestr("%s/%s.yar" % (signature_directory, category), rules)

        if ips:
            z.writestr(ip_text_filename, "\n".join([ip.encode("utf-8") for ip in ips]))

        if dns:
            z.writestr(dns_text_filename, "\n".join([d.encode("utf-8") for d in dns]))

        return memzip

    def __repr__(self):
        return '<Release %r>' % (self.id)


@listens_for(Release, "before_insert")
def generate_eventid(mapper, connect, target):
    target.release_data = str(target.release_data).encode("utf-8")
