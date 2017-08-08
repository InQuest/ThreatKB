from app import db
from app.routes import tags_mapping
from app.models.comments import Comments
import json

class Yara_rule(db.Model):
    __tablename__ = "yara_rules"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    state = db.Column(db.String(32), index=True)
    revision = db.Column(db.Integer(unsigned=True), default=1)
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

    tags = []
    addedTags = []
    removedTags = []

    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==Yara_rule.created_user_id")

    modified_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    modified_user = db.relationship('KBUser', foreign_keys=modified_user_id,
                                    primaryjoin="KBUser.id==Yara_rule.modified_user_id")

    comments = db.relationship("Comments", foreign_keys=[id],
                               primaryjoin="and_(Comments.entity_id==Yara_rule.id, Comments.entity_type=='%s')" % (
                               Comments.ENTITY_MAPPING["SIGNATURE"]),
                               lazy="dynamic")

    def to_dict(self):
        revisions = Yara_rule_history.query.filter_by(yara_rule_id=self.id).all()
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
            condition="condition:\n\t%s" % self.condition,
            strings="strings:\n\t%s" % self.strings,
            id=self.id,
            tags=tags_mapping.get_tags_for_source(self.__tablename__, self.id),
            addedTags=[],
            removedTags=[],
            comments=[comment.to_dict() for comment in self.comments],
            revisions=[revision.to_dict() for revision in revisions],
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict(),
            revision=self.revision
        )

    def to_revision_dict(self):
        dict = self.to_dict()
        del dict["comments"]
        del dict["revisions"]
        del dict["tags"]
        del dict["removedTags"]
        del dict["addedTags"]
        return dict

    def __repr__(self):
        return '<Yara_rule %r>' % (self.id)

    @staticmethod
    def make_yara_sane(text, type_):
        type_ = "%s:" if not type_.endswith(":") else type_
        return "\n\t".join([string.strip().strip("\t") for string in text.split("\n") if type_ not in string]).strip()


class Yara_rule_history(db.Model):
    __tablename__ = "yara_rules_history"

    id = db.Column(db.Integer, primary_key=True)

    date_created = db.Column(db.DateTime(timezone=True))
    revision = db.Column(db.Integer(unsigned=True))

    rule_json = db.Column(db.Text, nullable=False)

    yara_rule_id = db.Column(db.Integer, db.ForeignKey("yara_rules.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    user = db.relationship('KBUser', foreign_keys=user_id,
                           primaryjoin="KBUser.id==Yara_rule_history.user_id")

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            revision=self.revision,
            rule_json=json.loads(self.rule_json),
            yara_rule_id=self.yara_rule_id,
            user=self.user.to_dict()
        )

    def __repr__(self):
        return '<Yara_rule_history %r>' % (self.id)
