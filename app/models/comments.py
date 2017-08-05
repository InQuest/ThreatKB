from app import db


class Comments(db.Model):
    ENTITY_MAPPING = {"SIGNATURE": 1, "DNS": 2, "IP": 3}

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    comment = db.Column(db.String(65000))
    entity_type = db.Column(db.Integer(), index=True, nullable=False)
    entity_id = db.Column(db.Integer(), index=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)

    user = db.relationship('KBUser', foreign_keys=user_id)

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            comment=self.comment,
            entity_type=self.ENTITY_MAPPING.keys()[self.ENTITY_MAPPING.values().index(self.entity_type)],
            entity_id=self.entity_id,
            id=self.id,
            user=self.user.to_dict()
        )

    def __repr__(self):
        return '<Comments %r>' % (self.id)
