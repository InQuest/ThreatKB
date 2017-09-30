from app import db

class Cfg_settings(db.Model):
    __tablename__ = "cfg_settings"

    key = db.Column(db.String(256), index=True, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    public = db.Column(db.Boolean, index=True, default=True)
    value = db.Column(db.String(2048))

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            key=self.key,
            value=self.value,
        )

    def __repr__(self):
        return '<Cfg_settings %s>' % (self.key)

    @staticmethod
    def get_private_setting(key):
        setting = db.session.query(Cfg_settings).filter(Cfg_settings.public == False).filter(
            Cfg_settings.key == key).first()
        return setting.value if setting else None

    @staticmethod
    def get_setting(key):
        setting = db.session.query(Cfg_settings).filter(Cfg_settings.key == key).first()
        return setting.value if setting else None
