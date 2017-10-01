from app import db


class Whitelist(db.Model):
    __tablename__ = "whitelist"

    # created_time
    # modified_time
    # created_by_user
    # modified_by_user
    # whitelist_artifact
    # notes

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    whitelist_artifact = db.Column(db.String(2048))
    notes = db.Column(db.String(2048))

    created_by_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_by_user = db.relationship('KBUser', foreign_keys=created_by_user_id,
                                      primaryjoin="KBUser.id==Whitelist.created_by_user_id")
    modified_by_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    modified_by_user = db.relationship('KBUser', foreign_keys=modified_by_user_id,
                                       primaryjoin="KBUser.id==Whitelist.modified_by_user_id")
    created_time = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    modified_time = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())

    def to_dict(self):
        return dict(
            id=self.id,
            whitelist_artifact=self.whitelist_artifact,
            notes=self.notes,
            created_by_user=self.created_by_user.to_dict(),
            modified_by_user=self.modified_by_user.to_dict(),
            created_time=self.created_time.isoformat(),
            modified_time=self.modified_time.isoformat()
        )
