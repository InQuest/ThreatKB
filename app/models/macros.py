from app import db


class Macros(db.Model):
    __tablename__ = "macros"

    tag = db.Column(db.String(512), index=True, primary_key=True)
    value = db.Column(db.TEXT())
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())

    def to_dict(self):
        return dict(
            tag=self.tag,
            value=self.value,
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat()
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
