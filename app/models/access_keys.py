from app import db


class AccessKeys(db.Model):
    __tablename__ = "access_keys"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    user = db.relationship('KBUser', foreign_keys=user_id, primaryjoin="KBUser.id==AccessKeys.user_id")
    token = db.Column(db.String(255), unique=True, nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    deleted = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.Enum('active', 'inactive', 'deleted'), default='active')

    def to_dict(self):
        return dict(
            id=self.id,
            user=self.user.to_dict(),
            token=self.token.decode('ascii'),
            created=self.created.isoformat(),
            deleted=None if not self.deleted else self.deleted.isoformat(),
            status=self.status
        )
