from app import db
from app.models import c2dns, c2ip, yara_rule, cfg_settings
from sqlalchemy import and_

import json


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
            created_user=self.created_user.to_dict()
        )

    def get_release_data(self):
        if self.release_data:
            return self.release_data

        release_state = Release.query.filter(Release.is_test_release > 0).first()
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
            "IP": {"IP": {entity.to_dict()["id"]: entity.to_dict() for entity in dns}, "Added": [], "Removed": [],
                   "Modified": []}}

        last_release = Release.query.filter(Release.is_test_release == 0).order_by(Release.id.desc()).first()

        if not last_release:
            release_data["Signatures"]["Added"] = release_data["Signatures"]["Signatures"]
            release_data["IP"]["Added"] = release_data["IP"]["IP"]
            release_data["DNS"]["Added"] = release_data["DNS"]["DNS"]
            return release_data

        last_release = json.loads(last_release.release_data)

        ##### SIGNATURES #######
        release_signature_ids = release_data["Signatures"]["Signatures"].keys()
        last_release_signature_ids = last_release["Signatures"]["Signatures"].keys()

        for signature in release_data["Signatures"]["Signatures"]:
            signature_id = signature["id"]
            if not signature_id in last_release_signature_ids:
                release_data["Signatures"]["Added"].append(signature)
            else:
                if signature["date_modified"] > self.date_created:
                    release_data["Signatures"]["Modified"].append(signature)
                del last_release["Signatures"]["Signatures"][signature_id]

        for signature in last_release["Signatures"]["Signatures"]:
            release_data["Signatures"]["Removed"].append(signature)

        ###### IPs ########
        release_ips = release_data["IP"]["IP"].keys()
        last_release_ips = last_release["IP"]["IP"].keys()

        for ip in release_data["IP"]["IP"]:
            ip_id = ip["id"]
            if not ip_id in last_release_ips:
                release_data["IP"]["Added"].append(ip)
            else:
                if ip["date_modified"] > self.date_created:
                    release_data["IP"]["Modified"].append(ip)
                del last_release["IP"]["IP"][ip_id]

        for ip in last_release["IP"]["IP"]:
            release_data["IP"]["Removed"].append(ip)

        ###### DNS #######
        release_dns = release_data["DNS"]["DNS"].keys()
        last_release_dns = last_release["DNS"]["DNS"].keys()

        for dns in release_data["DNS"]["DNS"]:
            dns_id = dns["id"]
            if not dns_id in last_release_dns:
                release_data["DNS"]["Added"].append(dns)
            else:
                if ip["date_modified"] > self.date_created:
                    release_data["DNS"]["Modified"].append(dns)
                del last_release["DNS"]["DNS"][dns_id]

        for ip in last_release["DNS"]["DNS"]:
            release_data["DNS"]["Removed"].append(ip)

        return json.dumps(release_data)

    def generate_release_notes(self):
        prepend_text = cfg_settings.Cfg_settings.query.filter(and_(cfg_settings.Cfg_settings.public == False,
                                                                   cfg_settings.Cfg_settings.key == "RELEASE_PREPEND_TEXT")).first()
        postpend_text = cfg_settings.Cfg_settings.query.filter(and_(cfg_settings.Cfg_settings.public == False,
                                                                    cfg_settings.Cfg_settings.key == "RELEASE_POSTPEND_TEXT")).first()

        message = prepend_text.value if prepend_text else ""
        message += "New Signatures\n%s" % "-" * 10
        message += "\n\n".join(["EventID: %s\nName: %s\nCategory: %s\nConfidence: %s\nSeverity: %s\nDescription: %s" % (
        entity["signature_id"], entity["name"], entity["category"], entity["confidence"], entity["severity"],
        entity["description"]) for entity in self.release_data_dict["Signatures"]["Added"]]) if \
        self.release_data_dict["Signatures"]["Added"] else "NA"
        message += "\n\nRemoved Signatures\n%s" % "-" * 10
        message += "\n\n".join(["EventID: %s\nName: %s\nCategory: %s\nConfidence: %s\nSeverity: %s\nDescription: %s" % (
        entity["signature_id"], entity["name"], entity["category"], entity["confidence"], entity["severity"],
        entity["description"]) for entity in self.release_data_dict["Signatures"]["Removed"]]) if \
        self.release_data_dict["Signatures"]["Removed"] else "NA"
        message += "\n\nModified Signatures\n%s" % "-" * 10
        message += "\n\n".join(["EventID: %s\nName: %s\nCategory: %s\nConfidence: %s\nSeverity: %s\nDescription: %s" % (
        entity["signature_id"], entity["name"], entity["category"], entity["confidence"], entity["severity"],
        entity["description"]) for entity in self.release_data_dict["Signatures"]["Modified"]]) if \
        self.release_data_dict["Signatures"]["Modified"] else "NA"

        message += "Feed Content\n%s" % "-" * 10
        message += "C2IPs Added: %s\n" % (len(self.release_data_dict["IP"]["Added"]))
        message += "C2IPs Removed: %s\n" % (len(self.release_data_dict["IP"]["Removed"]))
        message += "C2 Domains Added: %s\n" % (len(self.release_data_dict["DNS"]["Added"]))
        message += "C2 Domains Removed: %s\n" % (len(self.release_data_dict["DNS"]["Removed"]))

        return message

    def generate_signature_export(self):
        pass

    def __repr__(self):
        return '<Tags %r>' % (self.id)
