from app import db
from app.models.comments import Comments


class Yara_rule(db.Model):
    __tablename__ = "yara_rules"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    state = db.Column(db.String(32), index=True)
    name = db.Column(db.String(128), index=True)
    test_status = db.Column(db.String(16))
    confidence = db.Column(db.Integer)
    severity = db.Column(db.Integer)
    description = db.Column(db.String(4096))
    category = db.Column(db.String(32))
    file_type = db.Column(db.String(32))
    subcategory1 = db.Column(db.String(32))
    subcategory2 = db.Column(db.String(32))
    subcategory3 = db.Column(db.String(32))
    reference_link = db.Column(db.String(2048))
    reference_text = db.Column(db.String(2048))
    condition = db.Column(db.String(2048))
    strings = db.Column(db.String(30000))

    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==Yara_rule.created_user_id")

    modified_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    modified_user = db.relationship('KBUser', foreign_keys=modified_user_id,
                                    primaryjoin="KBUser.id==Yara_rule.modified_user_id")

    comments = db.relationship("Comments", foreign_keys=[id],
                               primaryjoin="and_(Comments.entity_id==Yara_rule.id, Comments.entity_type=='%s')" % (
                               Comments.ENTITY_MAPPING["SIGNATURE"]), lazy="dynamic")

    def to_dict(self):
        comments = Comments.query.filter_by(entity_id=self.id).filter_by(
            entity_type=Comments.ENTITY_MAPPING["SIGNATURE"]).all()
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            state=self.state,
            name=self.name,
            test_status=self.test_status,
            confidence=self.confidence,
            severity=self.severity,
            description=self.description,
            category=self.category,
            file_type=self.file_type,
            subcategory1=self.subcategory1,
            subcategory2=self.subcategory2,
            subcategory3=self.subcategory3,
            reference_link=self.reference_link,
            reference_text=self.reference_text,
            condition=self.condition,
            strings=self.strings,
            id=self.id,
            comments=[comment.to_dict() for comment in self.comments],
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict()
        )

    def __repr__(self):
        return '<Yara_rule %r>' % (self.id)
