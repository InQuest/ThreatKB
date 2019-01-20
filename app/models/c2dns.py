import distutils
import re

from ipaddr import IPAddress, IPNetwork
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session

import app
from app import db, current_user, ENTITY_MAPPING, ACTIVITY_TYPE
from app.models.whitelist import Whitelist
from app.models.metadata import Metadata, MetadataMapping
from app.routes import tags_mapping
from app.models.comments import Comments
from app.models import cfg_states, cfg_settings, activity_log

from flask import abort

import time


class C2dns(db.Model):
    __tablename__ = "c2dns"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    state = db.Column(db.String(32), index=True)
    domain_name = db.Column(db.String(2048), index=True, unique=True)
    match_type = db.Column(db.Enum('exact', 'wildcard'))
    description = db.Column(db.TEXT())
    references = db.Column(db.TEXT())
    expiration_type = db.Column(db.String(32))
    expiration_timestamp = db.Column(db.DateTime(timezone=True))

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
                                   ENTITY_MAPPING["DNS"]))

    tags = []

    WHITELIST_CACHE = None
    WHITELIST_CACHE_LAST_UPDATE = None

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

    def save_metadata(self, metadata):
        for name, val in metadata.iteritems():
            val = val if not type(val) == dict else val.get("value", None)
            if not val:
                continue

            m = db.session.query(MetadataMapping).join(Metadata, Metadata.id == MetadataMapping.metadata_id).filter(
                Metadata.key == name).filter(Metadata.artifact_type == ENTITY_MAPPING["DNS"]).filter(
                MetadataMapping.artifact_id == self.id).first()
            if m:
                m.value = val
                db.session.add(m)
                dirty = True
            else:
                m = db.session.query(Metadata).filter(Metadata.key == name).filter(
                    Metadata.artifact_type == ENTITY_MAPPING["DNS"]).first()
                db.session.add(MetadataMapping(value=val, metadata_id=m.id, artifact_id=self.id,
                                               created_user_id=current_user.id))

        try:
            db.session.commit()
        except Exception as e:
            app.logger.exception(e)

    @staticmethod
    def get_metadata_to_save(artifact, metadata, metadata_cache={}, user_cache={}):
        metadata_to_save = []
        metas = {}

        for meta in db.session.query(Metadata).all():
            if not meta.artifact_type in metas.keys():
                metas[meta.artifact_type] = {}
            metas[meta.artifact_type][meta.key] = meta

        for name, val in metadata.iteritems():
            val = val if not type(val) == dict else val["value"]

            if metadata_cache:
                m = metadata_cache["DNS"].get(artifact.id, {}).get("metadata_values", {}).get(name, None)
            else:
                m = db.session.query(MetadataMapping).join(Metadata, Metadata.id == MetadataMapping.metadata_id).filter(
                    Metadata.key == name).filter(Metadata.artifact_type == ENTITY_MAPPING["DNS"]).filter(
                    MetadataMapping.artifact_id == artifact.id).first()

            if m:
                m.value = val
                metadata_to_save.append(m)
            else:
                m = metas.get(ENTITY_MAPPING["DNS"], {}).get(name, None)
                # m = db.session.query(Metadata).filter(Metadata.key == name).filter(
                #    Metadata.artifact_type == ENTITY_MAPPING["DNS"]).first()
                if m:
                    metadata_to_save.append(MetadataMapping(value=val, metadata_id=m.id, artifact_id=artifact.id,
                                                            created_user_id=current_user.id))
        return metadata_to_save

    def to_dict(self, include_metadata=True):
        d = dict(
            date_created=self.date_created.isoformat() if self.date_created else None,
            date_modified=self.date_modified.isoformat() if self.date_modified else None,
            state=self.state,
            domain_name=self.domain_name,
            match_type=self.match_type,
            expiration_type=self.expiration_type,
            expiration_timestamp=self.expiration_timestamp.isoformat() if self.expiration_timestamp else None,
            id=self.id,
            tags=tags_mapping.get_tags_for_source(self.__tablename__, self.id),
            description=self.description,
            references=self.references,
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict(),
            owner_user=self.owner_user.to_dict() if self.owner_user else None,
            comments=[comment.to_dict() for comment in
                      Comments.query.filter_by(entity_id=self.id).filter_by(entity_type=ENTITY_MAPPING["DNS"]).all()],
        )

        if include_metadata:
            metadata_values_dict = {}
            metadata_keys = Metadata.get_metadata_keys("DNS")
            metadata_values_dict = {m["metadata"]["key"]: m for m in
                                    [entity.to_dict() for entity in self.metadata_values]}
            for key in list(set(metadata_keys) - set(metadata_values_dict.keys())):
                metadata_values_dict[key] = {}
            d.update(dict(metadata=Metadata.get_metadata_dict("DNS"), metadata_values=metadata_values_dict))

        return d

    def to_release_dict(self, metadata_cache, user_cache):
        return dict(
            date_created=self.date_created.isoformat() if self.date_created else None,
            date_modified=self.date_modified.isoformat() if self.date_modified else None,
            state=self.state,
            domain_name=self.domain_name,
            match_type=self.match_type,
            expiration_type=self.expiration_type,
            description=self.description,
            references=self.references,
            expiration_timestamp=self.expiration_timestamp.isoformat() if self.expiration_timestamp else None,
            id=self.id,
            created_user=user_cache[self.created_user_id],
            modified_user=user_cache[self.modified_user_id],
            owner_user=user_cache[self.owner_user_id] if self.owner_user_id else None,
            metadata=metadata_cache["DNS"][self.id]["metadata"] if metadata_cache["DNS"].get(self.id, None) and
                                                                   metadata_cache["DNS"][self.id].get("metadata",
                                                                                                      None) else {},
            metadata_values=metadata_cache["DNS"][self.id]["metadata_values"] if metadata_cache["DNS"].get(self.id,
                                                                                                           None) and
                                                                                 metadata_cache["DNS"][self.id].get(
                                                                                     "metadata_values", None) else {},
        )

    @classmethod
    def get_c2dns_from_hostname(cls, hostname, metadata_field_mapping):
        artifact = None
        if type(hostname) is dict:
            artifact = hostname
            hostname = hostname["artifact"]

        c2dns = C2dns()
        c2dns.domain_name = hostname

        if artifact and metadata_field_mapping:
            for key, val in metadata_field_mapping.iteritems():
                try:
                    setattr(c2dns, val, artifact["metadata"][key])
                except:
                    pass

        return c2dns

    def __repr__(self):
        return '<C2dns %r>' % (self.id)


@listens_for(C2dns, "before_insert")
def run_against_whitelist(mapper, connect, target):
    whitelist_enabled = cfg_settings.Cfg_settings.get_setting("ENABLE_DNS_WHITELIST_CHECK_ON_SAVE")
    whitelist_states = cfg_settings.Cfg_settings.get_setting("WHITELIST_STATES")

    if whitelist_enabled and distutils.util.strtobool(whitelist_enabled) and whitelist_states:
        states = []
        for s in whitelist_states.split(","):
            if hasattr(cfg_states.Cfg_states, s):
                result = cfg_states.Cfg_states.query.filter(getattr(cfg_states.Cfg_states, s) > 0).first()
                if result:
                    states.append(result.state)

        if target.state in states:
            domain_name = target.domain_name
            target.domain_name = str(target.domain_name).lower()

            abort_import = False

            if not C2dns.WHITELIST_CACHE_LAST_UPDATE or not C2dns.WHITELIST_CACHE \
                    or (time.time() - C2dns.WHITELIST_CACHE_LAST_UPDATE) > 60:
                C2dns.WHITELIST_CACHE = Whitelist.query.all()
                C2dns.WHITELIST_CACHE_LAST_UPDATE = time.time()

            whitelists = C2dns.WHITELIST_CACHE

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


@listens_for(C2dns, "after_insert")
def dns_created(mapper, connection, target):
    activity_log.log_activity(connection=connection,
                              activity_type=ACTIVITY_TYPE.keys()[ACTIVITY_TYPE.keys().index("ARTIFACT_CREATED")],
                              activity_text=target.domain_name,
                              activity_date=target.date_created,
                              entity_type=ENTITY_MAPPING["DNS"],
                              entity_id=target.id,
                              user_id=target.created_user_id)


@listens_for(C2dns, "after_update")
def dns_modified(mapper, connection, target):
    session = Session.object_session(target)

    if session.is_modified(target, include_collections=False):
        state_activity_text = activity_log.get_state_change(target, target.domain_name)
        if state_activity_text:
            activity_log.log_activity(connection=connection,
                                      activity_type=ACTIVITY_TYPE.keys()[ACTIVITY_TYPE.keys().index("STATE_TOGGLED")],
                                      activity_text=state_activity_text,
                                      activity_date=target.date_modified,
                                      entity_type=ENTITY_MAPPING["DNS"],
                                      entity_id=target.id,
                                      user_id=target.modified_user_id)

        changes = activity_log.get_modified_changes(target)
        if changes.__len__() > 0:
            activity_log.log_activity(connection=connection,
                                      activity_type=ACTIVITY_TYPE.keys()[ACTIVITY_TYPE.keys().index("ARTIFACT_MODIFIED")],
                                      activity_text="'%s' modified with changes: %s"
                                                    % (target.domain_name, ', '.join(map(str, changes))),
                                      activity_date=target.date_modified,
                                      entity_type=ENTITY_MAPPING["DNS"],
                                      entity_id=target.id,
                                      user_id=target.modified_user_id)
