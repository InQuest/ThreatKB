import re

from ipaddr import IPAddress, IPNetwork
from sqlalchemy.event import listens_for

from app import db
from app.models.whitelist import Whitelist
from app.routes import tags_mapping
from app.models.comments import Comments

import ipwhois


class C2ip(db.Model):
    __tablename__ = "c2ip"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    ip = db.Column(db.String(15), index=True, unique=True)
    asn = db.Column(db.String(128))
    country = db.Column(db.String(64))
    state = db.Column(db.String(32), index=True)
    reference_link = db.Column(db.String(2048))
    expiration_type = db.Column(db.String(32))
    expiration_timestamp = db.Column(db.DateTime(timezone=True))

    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==C2ip.created_user_id")

    modified_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    modified_user = db.relationship('KBUser', foreign_keys=modified_user_id,
                                    primaryjoin="KBUser.id==C2ip.modified_user_id")

    owner_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=True)
    owner_user = db.relationship('KBUser', foreign_keys=owner_user_id,
                                    primaryjoin="KBUser.id==C2ip.owner_user_id")

    comments = db.relationship("Comments", foreign_keys=[id],
                               primaryjoin="and_(Comments.entity_id==C2ip.id, Comments.entity_type=='%s')" % (
                               Comments.ENTITY_MAPPING["IP"]), lazy="dynamic")

    tags = []

    addedTags = []

    removedTags = []

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            ip=self.ip,
            asn=self.asn,
            country=self.country,
            state=self.state,
            reference_link=self.reference_link,
            expiration_type=self.expiration_type,
            expiration_timestamp=self.expiration_timestamp.isoformat() if self.expiration_timestamp else None,
            id=self.id,
            tags=tags_mapping.get_tags_for_source(self.__tablename__, self.id),
            addedTags=[],
            removedTags=[],
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict(),
            owner_user=self.owner_user.to_dict() if self.owner_user else None,
            comments=[comment.to_dict() for comment in self.comments]
        )

    @classmethod
    def get_c2ip_from_ip(cls, ip):
        whois = ipwhois.IPWhois(ip).lookup_whois()

        c2ip = C2ip()
        c2ip.ip = ip
        c2ip.asn = whois.get("asn_description", None)

        net = {}
        for range in whois.get("nets", []):
            if range["cidr"] == whois["asn_cidr"]:
                net = range
                break

        c2ip.country = net.get("country", None)
        c2ip.city = net.get("city", None)
        c2ip.state = net.get("state", None)
        return c2ip


    def __repr__(self):
        return '<C2ip %r>' % (self.id)


@listens_for(C2ip, "before_insert")
def run_against_whitelist(mapper, connect, target):
    new_ip = target.ip

    abort_import = False

    whitelists = Whitelist.query.all()
    for whitelist in whitelists:
        wa = str(whitelist.whitelist_artifact)

        try:
            if str(IPAddress(new_ip)) == str(IPAddress(wa)):
                abort_import = True
                break
        except ValueError:
            pass

        try:
            if IPAddress(new_ip) in IPNetwork(wa):
                abort_import = True
                break
        except ValueError:
            pass

        regex = re.compile(wa)
        result = regex.match(new_ip)
        if result:
            abort_import = True
            break

    if abort_import:
        raise Exception('Failed Whitelist Validation')
