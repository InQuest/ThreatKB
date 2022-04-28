from app import db, ENTITY_MAPPING


class Bookmarks(db.Model):
    __tablename__ = "bookmarks"


    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.Integer(), index=True, nullable=False)
    entity_id = db.Column(db.Integer(), index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    user = db.relationship('KBUser', foreign_keys=user_id)

    def to_dict(self, artifact_name=None, permalink_prefix=None):
        return dict(
            artifact_name=artifact_name,
            entity_type=list(ENTITY_MAPPING.keys())[list(ENTITY_MAPPING.values()).index(self.entity_type)],
            entity_id=self.entity_id,
            permalink_prefix=permalink_prefix,
            user=self.user.to_dict(),
            id=self.id
        )

    def __repr__(self):
        return '<bookmarks %r>' % self.id
