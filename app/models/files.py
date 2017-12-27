from app import db, ENTITY_MAPPING


class Files(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True),
                             default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True),
                              default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    filename = db.Column(db.String(65000))
    content_type = db.Column(db.String(100))
    entity_type = db.Column(db.Integer(unsigned=True), index=True, nullable=True)
    entity_id = db.Column(db.Integer(unsigned=True), index=True, nullable=True)
    sha256 = db.Column(db.String(64), nullable=True)
    md5 = db.Column(db.String(32), nullable=True)
    sha1 = db.Column(db.String(40), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    user = db.relationship('KBUser', foreign_keys=user_id)

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            filename=self.filename,
            content_type=self.content_type,
            entity_type=ENTITY_MAPPING.keys()[ENTITY_MAPPING.values().index(self.entity_type)]
            if self.entity_type else None,
            entity_id=self.entity_id if self.entity_id else None,
            id=self.id,
            user=self.user.to_dict(),
            sha1=self.sha1,
            md5=self.md5,
            sha256=self.sha256
        )

    def __repr__(self):
        return '<Files %r>' % self.id
