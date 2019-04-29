from app import db


class Macros(db.Model):
    __tablename__ = "macros"

    tag = db.Column(db.String(512), index=True, primary_key=True)
    value = db.Column(db.TEXT())
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())

    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==Macros.created_user_id")

    modified_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    modified_user = db.relationship('KBUser', foreign_keys=modified_user_id,
                                    primaryjoin="KBUser.id==Macros.modified_user_id")

    def to_dict(self):
        return dict(
            tag=self.tag,
            value=self.value,
            active=self.active,
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict()
        )

    def __repr__(self):
        return '<Marcos %s>' % self.tag

    @staticmethod
    def get_value(tag):
        try:
            setting = db.session.query(Macros).filter(Macros.tag == tag).first()
            return setting.value if setting else None
        except:
            return None

    @staticmethod
    def get_macros():
        try:
            entities = db.session.query(Macros).all()
            return [entity.to_dict() for entity in entities]
        except:
            return None
