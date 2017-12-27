from app import db, ENTITY_MAPPING


class Comments(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    comment = db.Column(db.String(65000))
    entity_type = db.Column(db.Integer(unsigned=True), index=True, nullable=False)
    entity_id = db.Column(db.Integer(unsigned=True), index=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)

    user = db.relationship('KBUser', foreign_keys=user_id)

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            comment=self.comment,
            entity_type=ENTITY_MAPPING.keys()[ENTITY_MAPPING.values().index(self.entity_type)],
            entity_id=self.entity_id,
            id=self.id,
            user=self.user.to_dict()
        )

    def __repr__(self):
        return '<Comments %r>' % (self.id)
