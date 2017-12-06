from app import db


class Scripts(db.Model):
    __tablename__ = "scripts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(128), nullable=True)
    code = db.Column(db.String(60000), nullable=True)
    match_regex = db.Column(db.String(4096), nullable=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==Scripts.created_user_id")

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            description=self.description,
            code=self.code,
            match_regex=self.match_regex,
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            created_user=self.created_user.to_dict(),
        )

    def __repr__(self):
        return '<Script %r>' % (self.id)
