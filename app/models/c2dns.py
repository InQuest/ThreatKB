import re

from ipaddr import IPAddress, IPNetwork
from sqlalchemy.event import listens_for

from app import db, current_user, ENTITY_MAPPING
from app.models.whitelist import Whitelist
from app.models.metadata import Metadata, MetadataMapping
from app.routes import tags_mapping
from app.models.comments import Comments
from app.models import cfg_states

from flask import abort

class C2dns(db.Model):
    __tablename__ = "c2dns"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    state = db.Column(db.String(32), index=True)
    domain_name = db.Column(db.String(2048), index=True, unique=True)
    match_type = db.Column(db.Enum('exact', 'wildcard'))
    expiration_type = db.Column(db.String(32))
    expiration_timestamp = db.Column(db.DateTime(timezone=True))
    description = db.Column(db.String(512))

    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==C2dns.created_user_id")

    modified_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    modified_user = db.relationship('KBUser', foreign_keys=modified_user_id,
                                    primaryjoin="KBUser.id==C2dns.modified_user_id")

    owner_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=True)
    owner_user = db.relationship('KBUser', foreign_keys=owner_user_id,
                                    primaryjoin="KBUser.id==C2dns.owner_user_id")

    comments = db.relationship("Comments", foreign_keys=[id],
                               primaryjoin="and_(Comments.entity_id==C2dns.id, Comments.entity_type=='%s')" % (
                                   ENTITY_MAPPING["DNS"]), lazy="dynamic")

    tags = []
    addedTags = []
    removedTags = []

    @property
    def metadata_fields(self):
        return db.session.query(Metadata).filter(Metadata.artifact_type == ENTITY_MAPPING["DNS"]).all()

    @property
    def metadata_values(self):
        return db.session.query(MetadataMapping)\
            .join(Metadata, Metadata.id == MetadataMapping.metadata_id)\
            .filter(Metadata.active > 0)\
            .filter(Metadata.artifact_type == ENTITY_MAPPING["DNS"])\
            .filter(MetadataMapping.artifact_id == self.id)\
            .all()

    def to_dict(self):
        metadata_values_dict = {}
        metadata_keys = Metadata.get_metadata_keys("DNS")
        metadata_values_dict = {m["metadata"]["key"]: m for m in [entity.to_dict() for entity in self.metadata_values]}
        for key in list(set(metadata_keys) - set(metadata_values_dict.keys())):
            metadata_values_dict[key] = {}

        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            state=self.state,
            domain_name=self.domain_name,
            match_type=self.match_type,
            expiration_type=self.expiration_type,
            expiration_timestamp=self.expiration_timestamp.isoformat() if self.expiration_timestamp else None,
            description=self.description,
            id=self.id,
            tags=tags_mapping.get_tags_for_source(self.__tablename__, self.id),
            addedTags=[],
            removedTags=[],
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict(),
            owner_user=self.owner_user.to_dict() if self.owner_user else None,
            comments=[comment.to_dict() for comment in
                      Comments.query.filter_by(entity_id=self.id).filter_by(entity_type=ENTITY_MAPPING["DNS"]).all()],
            metadata=Metadata.get_metadata_dict("DNS"),
            metadata_values=metadata_values_dict,
        )

    def to_release_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            state=self.state,
            domain_name=self.domain_name,
            match_type=self.match_type,
            expiration_type=self.expiration_type,
            description=self.description,
            expiration_timestamp=self.expiration_timestamp.isoformat() if self.expiration_timestamp else None,
            id=self.id
        )

    @classmethod
    def get_c2dns_from_hostname(cls, hostname):
        c2dns = C2dns()
        c2dns.domain_name = hostname
        return c2dns

    def __repr__(self):
        return '<C2dns %r>' % (self.id)


@listens_for(C2dns, "before_insert")
def run_against_whitelist(mapper, connect, target):
    domain_name = target.domain_name

    abort_import = False

    whitelists = Whitelist.query.all()
    for whitelist in whitelists:
        wa = str(whitelist.whitelist_artifact)

        try:
            ip = IPAddress(wa)
            continue
        except ValueError:
            pass

        try:
            cidr = IPNetwork(wa)
            continue
        except ValueError:
            pass

        try:
            regex = re.compile(wa)
            result = regex.search(domain_name)
        except:
            result = False

        if result:
            abort_import = True
            break

    if abort_import:
        raise Exception('Failed Whitelist Validation')

    if not current_user.admin:
        release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
        if release_state and target.state == release_state.state:
            abort(403)


@listens_for(C2dns, "before_update")
def c2dns_before_update(mapper, connect, target):
    if not current_user.admin:
        release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
        if release_state and target.state == release_state.state:
            abort(403)
