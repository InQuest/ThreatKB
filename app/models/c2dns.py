from app import db
from app.routes import tags_mapping
from app.models.comments import Comments

class C2dns(db.Model):
    __tablename__ = "c2dns"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    state = db.Column(db.String(32), index=True)
    domain_name = db.Column(db.String(2048), index=True, unique=True)
    match_type = db.Column(db.Enum('exact', 'wildcard'))
    reference_link = db.Column(db.String(2048))
    reference_text = db.Column(db.String(2048))
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
                               Comments.ENTITY_MAPPING["DNS"]), lazy="dynamic")

    tags = []

    addedTags = []

    removedTags = []

    def to_dict(self):
        comments = Comments.query.filter_by(entity_id=self.id).filter_by(
            entity_type=Comments.ENTITY_MAPPING["DNS"]).all()
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            state=self.state,
            domain_name=self.domain_name,
            match_type=self.match_type,
            reference_link=self.reference_link,
            reference_text=self.reference_text,
            expiration_type=self.expiration_type,
            expiration_timestamp=self.expiration_timestamp.isoformat() if self.expiration_timestamp else None,
            id=self.id,
            tags=tags_mapping.get_tags_for_source(self.__tablename__, self.id),
            addedTags=[],
            removedTags=[],
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict(),
            owner_user=self.owner_user.to_dict() if self.owner_user else None,
            comments=[comment.to_dict() for comment in comments]
        )

    @classmethod
    def get_c2dns_from_hostname(cls, hostname):
        c2dns = C2dns()
        c2dns.domain_name = hostname
        return c2dns

    def __repr__(self):
        return '<C2dns %r>' % (self.id)
