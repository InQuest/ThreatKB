from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session

import app
from app import db, current_user, ENTITY_MAPPING, ACTIVITY_TYPE
from app.geo_ip_helper import get_geo_for_ip
from app.models.comments import Comments
from app.models.whitelist import Whitelist, WhitelistException
from app.routes import tags_mapping
from app.models.metadata import Metadata, MetadataMapping
from app.models import cfg_states, activity_log
from ipaddr import IPAddress, IPNetwork
from app.models import cfg_states, cfg_settings, activity_log
from app.routes.countries import get_country
from flask import abort


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
    description = db.Column(db.TEXT())
    references = db.Column(db.TEXT())
    expiration_timestamp = db.Column(db.DateTime(timezone=True))
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)

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
                                   ENTITY_MAPPING["IP"]), uselist=True)

    tags = []

    @property
    def metadata_fields(self):
        return db.session.query(Metadata).filter(Metadata.artifact_type == ENTITY_MAPPING["IP"]).all()

    @property
    def metadata_values(self):
        return db.session.query(MetadataMapping)\
            .join(Metadata, Metadata.id == MetadataMapping.metadata_id)\
            .filter(Metadata.active > 0) \
            .filter(Metadata.artifact_type == ENTITY_MAPPING["IP"])\
            .filter(MetadataMapping.artifact_id == self.id)\
            .all()

    def to_dict(self, include_metadata=True, include_tags=True, include_comments=True,
                metadata_cache=None, users_cache=None, tags_mapping_cache=None,
                comments_cache=None
                ):
        d = dict(
            active=self.active,
            date_created=self.date_created.isoformat() if self.date_created else None,
            date_modified=self.date_modified.isoformat() if self.date_modified else None,
            ip=self.ip,
            asn=self.asn,
            country=get_country(self.country),
            state=self.state,
            description=self.description,
            references=self.references,
            expiration_timestamp=self.expiration_timestamp.isoformat() if self.expiration_timestamp else None,
            id=self.id
        )

        if include_tags:
            if tags_mapping_cache and tags_mapping_cache['c2ip'].get(self.id, None):
                d["tags"] = tags_mapping_cache['c2ip'][self.id]
            else:
                d["tags"] = tags_mapping.get_tags_for_source(self.__tablename__, self.id)

        if include_comments:
            if comments_cache:
                d["comments"] = comments_cache['c2ip'][self.id] if self.id in comments_cache['c2ip'] else []
            else:
                d["comments"] = [comment.to_dict() for comment in Comments.query.filter_by(entity_id=self.id).filter_by(
                    entity_type=ENTITY_MAPPING["IP"]).all()]

        if include_metadata:
            if metadata_cache:
                d["metadata"] = metadata_cache["IP"][self.id]["metadata"] if metadata_cache["IP"].get(self.id, None) and metadata_cache["IP"][self.id].get("metadata",None) else {}
                d["metadata_values"] = metadata_cache["IP"][self.id]["metadata_values"] if metadata_cache["IP"].get(self.id,None) and metadata_cache["IP"][self.id].get("metadata_values", None) else {}
            else:
                metadata_values_dict = {}
                metadata_keys = Metadata.get_metadata_keys("IP")
                metadata_values_dict = {m["metadata"]["key"]: m for m in
                                        [entity.to_dict() for entity in self.metadata_values]}
                for key in list(set(metadata_keys) - set(metadata_values_dict.keys())):
                    metadata_values_dict[key] = {}
                d.update(dict(metadata=Metadata.get_metadata_dict("IP"), metadata_values=metadata_values_dict))

        if users_cache:
            d["created_user"] = users_cache.get(self.created_user_id, None)
            d["modified_user"] = users_cache.get(self.modified_user_id, None)
            d["owner_user"] = users_cache.get(self.owner_user_id, None)
        else:
            d["created_user"] = self.created_user.to_dict()
            d["modified_user"] = self.modified_user.to_dict()
            d["owner_user"] = self.owner_user.to_dict() if self.owner_user else None

        return d


    def to_release_dict(self, metadata_cache, user_cache):
        return dict(
            date_created=self.date_created.isoformat() if self.date_created else None,
            date_modified=self.date_modified.isoformat() if self.date_modified else None,
            ip=self.ip,
            asn=self.asn,
            country=get_country(self.country),
            state=self.state,
            description=self.description,
            references=self.references,
            expiration_timestamp=self.expiration_timestamp.isoformat() if self.expiration_timestamp else None,
            id=self.id,
            created_user=user_cache[self.created_user_id],
            modified_user=user_cache[self.modified_user_id],
            owner_user=user_cache[self.owner_user_id] if self.owner_user_id else None,
            metadata=metadata_cache["IP"][self.id]["metadata"] if metadata_cache["IP"].get(self.id, None) and
                                                                  metadata_cache["IP"][self.id].get("metadata",
                                                                                                    None) else {},
            metadata_values=metadata_cache["IP"][self.id]["metadata_values"] if metadata_cache["IP"].get(self.id,
                                                                                                         None) and
                                                                                metadata_cache["IP"][self.id].get(
                                                                                    "metadata_values", None) else {},

        )

    def save_metadata(self, metadata):
        for name, val in metadata.items():
            val = val if not type(val) == dict else val.get("value", None)
            #if not val:
            #    continue

            m = db.session.query(MetadataMapping).join(Metadata, Metadata.id == MetadataMapping.metadata_id).filter(
                Metadata.key == name).filter(Metadata.artifact_type == ENTITY_MAPPING["DNS"]).filter(
                MetadataMapping.artifact_id == self.id).first()
            if m:
                m.value = val
                db.session.add(m)
                dirty = True
            else:
                m = db.session.query(Metadata).filter(Metadata.key == name).filter(
                    Metadata.artifact_type == ENTITY_MAPPING["IP"]).first()
                db.session.add(MetadataMapping(value=val, metadata_id=m.id, artifact_id=self.id,
                                               created_user_id=current_user.id))
                dirty = True

        try:
            db.session.commit()
        except Exception as e:
            app.logger.exception(e)

    @staticmethod
    def get_metadata_to_save(artifact, metadata, metadata_cache={}, user_cache={}):
        metadata_to_save = []
        metas = {}

        for meta in db.session.query(Metadata).all():
            if not meta.artifact_type in list(metas.keys()):
                metas[meta.artifact_type] = {}
            metas[meta.artifact_type][meta.key] = meta

        for name, val in metadata.items():
            val = val if not type(val) == dict else val["value"]

            if metadata_cache:
                m = metadata_cache["IP"].get(artifact.id, {}).get("metadata_values", {}).get(name, None)
            else:
                m = db.session.query(MetadataMapping).join(Metadata, Metadata.id == MetadataMapping.metadata_id).filter(
                    Metadata.key == name).filter(Metadata.artifact_type == ENTITY_MAPPING["IP"]).filter(
                    MetadataMapping.artifact_id == artifact.id).first()

            if m:
                m.value = val
                metadata_to_save.append(m)
            else:
                m = metas.get(ENTITY_MAPPING["IP"], {}).get(name, None)
                # m = db.session.query(Metadata).filter(Metadata.key == name).filter(
                #    Metadata.artifact_type == ENTITY_MAPPING["IP"]).first()
                if m:
                    metadata_to_save.append(MetadataMapping(value=val, metadata_id=m.id, artifact_id=artifact.id,
                                                            created_user_id=current_user.id))
        return metadata_to_save

    @classmethod
    def get_c2ip_from_ip(cls, ip, metadata_field_mapping):
        artifact = None

        if type(ip) is dict:
            artifact = ip
            ip = ip["artifact"]

        geo_ip = get_geo_for_ip(str(ip))

        c2ip = C2ip()
        c2ip.ip = ip

        if artifact and metadata_field_mapping:
            for key, val in metadata_field_mapping.items():
                try:
                    setattr(c2ip, val, artifact["metadata"][key])
                except:
                    pass

        if hasattr(c2ip, "asn") and not c2ip.asn:
            c2ip.asn = geo_ip["asn"]
            c2ip.country = geo_ip["country_code"]

        return c2ip

    def __repr__(self):
        return '<C2ip %r>' % (self.id)


@listens_for(C2ip, "before_insert")
def run_against_whitelist(mapper, connect, target):
    if Whitelist.hits_whitelist(target.ip, target.state):
        abort(412, f"Failed whitelist validation {target.ip}")

    if not current_user.admin:
        release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
        if release_state and target.state == release_state.state:
            abort(403)


@listens_for(C2ip, "before_update")
def c2ip_before_update(mapper, connect, target):
    try:
        IPAddress(target.ip)
    except:
        abort(412, f"Not a welformed IP address {target.ip}")

    if Whitelist.hits_whitelist(target.ip, target.state):
        abort(412, f"Failed whitelist validation {target.ip}")

    if current_user and not current_user.admin:
        release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
        if release_state and target.state == release_state.state:
            abort(403)


@listens_for(C2ip, "after_insert")
def ip_created(mapper, connection, target):
    activity_log.log_activity(connection=connection,
                              activity_type=list(ACTIVITY_TYPE.keys())[list(ACTIVITY_TYPE.keys()).index("ARTIFACT_CREATED")],
                              activity_text=target.ip,
                              activity_date=target.date_created,
                              entity_type=ENTITY_MAPPING["IP"],
                              entity_id=target.id,
                              user_id=target.created_user_id)


@listens_for(C2ip, "after_update")
def ip_modified(mapper, connection, target):
    session = Session.object_session(target)

    if session.is_modified(target, include_collections=False):
        state_activity_text = activity_log.get_state_change(target, target.ip)
        if state_activity_text:
            activity_log.log_activity(connection=connection,
                                      activity_type=list(app.ACTIVITY_TYPE.keys())[list(ACTIVITY_TYPE.keys()).index("STATE_TOGGLED")],
                                      activity_text=state_activity_text,
                                      activity_date=target.date_modified,
                                      entity_type=ENTITY_MAPPING["IP"],
                                      entity_id=target.id,
                                      user_id=target.modified_user_id)

        changes = activity_log.get_modified_changes(target)
        if changes.__len__() > 0:
            activity_log.log_activity(connection=connection,
                                      activity_type=list(ACTIVITY_TYPE.keys())[list(ACTIVITY_TYPE.keys()).index("ARTIFACT_MODIFIED")],
                                      activity_text="'%s' modified with changes: %s"
                                                    % (target.ip, ', '.join(map(str, changes))),
                                      activity_date=target.date_modified,
                                      entity_type=ENTITY_MAPPING["IP"],
                                      entity_id=target.id,
                                      user_id=target.modified_user_id)
