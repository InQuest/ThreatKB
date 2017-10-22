from app import db, app
from app.models import c2dns, c2ip, yara_rule, cfg_settings, cfg_states
from sqlalchemy import and_
from dateutil import parser
import json
import datetime
import StringIO
import zipfile

class Release(db.Model):
    __tablename__ = "releases"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), nullable=False)
    is_test_release = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    release_data = db.Column(db.Text, nullable=False)

    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==Release.created_user_id")

    @property
    def release_data_dict(self):
        return json.loads(self.release_data) if self.release_data else {}

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            is_test_release=self.is_test_release,
            release_data=self.release_data,
            date_created=self.date_created.isoformat(),
            created_user=self.created_user.to_dict(),
            num_signatures=len(self.release_data_dict["Signatures"]["Signatures"]),
            num_ips=len(self.release_data_dict["IP"]["IP"]),
            num_dns=len(self.release_data_dict["DNS"]["DNS"])
        )

    def get_release_data(self):
        if self.release_data:
            return self.release_data

        release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
        if not release_state:
            raise Exception("You need to specify a production release state first.")

        dns = c2dns.C2dns.query.filter(c2dns.C2dns.state == release_state.state).all()
        ip = c2ip.C2ip.query.filter(c2ip.C2ip.state == release_state.state).all()
        yr = yara_rule.Yara_rule.query.filter(yara_rule.Yara_rule.state == release_state.state).all()

        release_data = {
            "Signatures": {"Signatures": {entity.to_dict()["id"]: entity.to_dict() for entity in yr}, "Added": [],
                           "Removed": [], "Modified": []},
            "DNS": {"DNS": {entity.to_dict()["id"]: entity.to_dict() for entity in dns}, "Added": [], "Removed": [],
                    "Modified": []},
            "IP": {"IP": {entity.to_dict()["id"]: entity.to_dict() for entity in ip}, "Added": [], "Removed": [],
                   "Modified": []}}

        last_release = Release.query.filter(Release.is_test_release == 0).order_by(Release.id.desc()).first()

        if not last_release:
            release_data["Signatures"]["Added"] = release_data["Signatures"]["Signatures"]
            release_data["IP"]["Added"] = release_data["IP"]["IP"]
            release_data["DNS"]["Added"] = release_data["DNS"]["DNS"]
            return json.dumps(release_data)

        last_release = last_release.release_data_dict

        ##### SIGNATURES #######
        release_eventids = release_data["Signatures"]["Signatures"].keys()
        last_release_eventids = [long(release_id) for release_id in
                                      last_release["Signatures"]["Signatures"].keys()]

        for signature in release_data["Signatures"]["Signatures"].values():
            eventid = signature["id"]
            if not eventid in last_release_eventids:
                release_data["Signatures"]["Added"].append(signature)
            else:
                if parser.parse(signature["last_revision_date"]) > datetime.datetime.now():
                    release_data["Signatures"]["Modified"].append(signature)
                del last_release["Signatures"]["Signatures"][str(eventid)]

        for signature in last_release["Signatures"]["Signatures"].values():
            release_data["Signatures"]["Removed"].append(signature)

        ###### IPs ########
        release_ips = release_data["IP"]["IP"].keys()
        last_release_ips = [long(release_id) for release_id in last_release["IP"]["IP"].keys()]

        for ip in release_data["IP"]["IP"].values():
            ip_id = ip["id"]
            if not ip_id in last_release_ips:
                release_data["IP"]["Added"].append(ip)
            else:
                if parser.parse(ip["date_modified"]) > datetime.datetime.now():
                    release_data["IP"]["Modified"].append(ip)
                del last_release["IP"]["IP"][str(ip_id)]

        for ip in last_release["IP"]["IP"].values():
            release_data["IP"]["Removed"].append(ip)

        ###### DNS #######
        release_dns = release_data["DNS"]["DNS"].keys()
        last_release_dns = [long(release_id) for release_id in last_release["DNS"]["DNS"].keys()]

        for dns in release_data["DNS"]["DNS"].values():
            dns_id = dns["id"]
            if not dns_id in last_release_dns:
                release_data["DNS"]["Added"].append(dns)
            else:
                if parser.parse(dns["date_modified"]) > datetime.datetime.now():
                    release_data["DNS"]["Modified"].append(dns)
                del last_release["DNS"]["DNS"][str(dns_id)]

        for ip in last_release["DNS"]["DNS"].values():
            release_data["DNS"]["Removed"].append(ip)

        return json.dumps(release_data)

    def generate_release_notes(self):
        prepend_text = cfg_settings.Cfg_settings.query.filter(and_(cfg_settings.Cfg_settings.public == False,
                                                                   cfg_settings.Cfg_settings.key == "RELEASE_PREPEND_TEXT")).first()
        postpend_text = cfg_settings.Cfg_settings.query.filter(and_(cfg_settings.Cfg_settings.public == False,
                                                                    cfg_settings.Cfg_settings.key == "RELEASE_POSTPEND_TEXT")).first()

        message = prepend_text.value if prepend_text else ""
        message += "New Signatures\n%s\n" % ("-" * 10)
        message += "\n\n".join(["EventID: %s\nName: %s\nCategory: %s\nConfidence: %s\nSeverity: %s\nDescription: %s" % (
            entity["eventid"], entity["name"], entity["category"], entity["confidence"], entity["severity"],
            entity["description"]) for entity in self.release_data_dict["Signatures"]["Added"]]) if \
            len(self.release_data_dict["Signatures"]["Added"]) > 0 else "NA"
        message += "\n\nRemoved Signatures\n%s\n" % ("-" * 10)
        message += "\n\n".join(["EventID: %s\nName: %s\nCategory: %s\nConfidence: %s\nSeverity: %s\nDescription: %s" % (
            entity["eventid"], entity["name"], entity["category"], entity["confidence"], entity["severity"],
            entity["description"]) for entity in self.release_data_dict["Signatures"]["Removed"]]) if \
            len(self.release_data_dict["Signatures"]["Removed"]) > 0 else "NA"
        message += "\n\nModified Signatures\n%s\n" % ("-" * 10)
        message += "\n\n".join(["EventID: %s\nName: %s\nCategory: %s\nConfidence: %s\nSeverity: %s\nDescription: %s" % (
            entity["eventid"], entity["name"], entity["category"], entity["confidence"], entity["severity"],
            entity["description"]) for entity in self.release_data_dict["Signatures"]["Modified"]]) if \
            len(self.release_data_dict["Signatures"]["Modified"]) > 0 else "NA"

        message += "\n\nFeed Content\n%s\n" % ("-" * 10)
        message += "C2IPs Added: %s\n" % (len(self.release_data_dict["IP"]["Added"]))
        message += "C2IPs Removed: %s\n" % (len(self.release_data_dict["IP"]["Removed"]))
        message += "C2 Domains Added: %s\n" % (len(self.release_data_dict["DNS"]["Added"]))
        message += "C2 Domains Removed: %s\n" % (len(self.release_data_dict["DNS"]["Removed"]))

        stream = StringIO.StringIO()
        stream.write(message)
        return stream

    def generate_artifact_export(self):
        release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
        ip_text_filename = cfg_settings.Cfg_settings.query.filter_by(key="EXPORT_FILENAME_IP").first()
        ip_text_filename = ip_text_filename.value if ip_text_filename else "IPs.txt"
        dns_text_filename = cfg_settings.Cfg_settings.query.filter_by(key="EXPORT_FILENAME_DNS").first()
        dns_text_filename = dns_text_filename.value if dns_text_filename else "DNS.txt"
        signature_directory = cfg_settings.Cfg_settings.query.filter_by(key="EXPORT_DIRECTORY_SIGNATURE").first()
        signature_directory = signature_directory.value if signature_directory else "signatures"

        if not release_state:
            raise Exception("You need to specify a production release state first.")

        combined_rules = {}
        for signature in self.release_data_dict["Signatures"]["Signatures"].values():
            category = signature.get("category")
            if not signature["category"] in combined_rules:
                combined_rules[category] = []

            combined_rules[category].append(signature)

        ips = [ip.get("ip") for ip in self.release_data_dict["IP"]["IP"].values()]
        ips.sort()

        dns = [dns.get("domain_name") for dns in self.release_data_dict["DNS"]["DNS"].values()]
        dns.sort()

        memzip = StringIO.StringIO()
        z = zipfile.ZipFile(memzip, mode="w", compression=zipfile.ZIP_DEFLATED)
        for category, rules in combined_rules.iteritems():
            rules = "\n\n".join([yara_rule.Yara_rule.to_yara_rule_string(signature) for signature in rules])
            z.writestr("%s/%s.yar" % (signature_directory, category), rules)

        if ips:
            z.writestr(ip_text_filename, "\n".join(ips))

        if dns:
            z.writestr(dns_text_filename, "\n".join(dns))

        return memzip

    def __repr__(self):
        return '<Release %r>' % (self.id)
