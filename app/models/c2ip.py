from app import db
from app.routes import tags_mapping
from app.models.comments import Comments

class C2ip(db.Model):
    __tablename__ = "c2ip"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    ip = db.Column(db.String(15), index=True)
    asn = db.Column(db.String(128))
    country = db.Column(db.String(64))
    city = db.Column(db.String(64))
    st = db.Column(db.String(32))
    state = db.Column(db.String(32), index=True)
    reference_link = db.Column(db.String(2048))
    reference_text = db.Column(db.String(2048))
    expiration_type = db.Column(db.String(32))
    expiration_timestamp = db.Column(db.DateTime(timezone=True))

    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==C2ip.created_user_id")

    modified_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    modified_user = db.relationship('KBUser', foreign_keys=modified_user_id,
                                    primaryjoin="KBUser.id==C2ip.modified_user_id")

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
            city=self.city,
            state=self.state,
            reference_link=self.reference_link,
            reference_text=self.reference_text,
            expiration_type=self.expiration_type,
            expiration_timestamp=self.expiration_timestamp.isoformat(),
            id=self.id,
            tags=tags_mapping.get_tags_for_source(self.__tablename__, self.id),
            addedTags=[],
            removedTags=[],
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict(),
            comments=[comment.to_dict() for comment in self.comments]
        )

    def __repr__(self):
        return '<C2ip %r>' % (self.id)
