from sqlalchemy import or_
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

    def is_associated_with_sig(self):
        from app.models import yara_rule, cfg_settings

        tag_template = cfg_settings.Cfg_settings.get_setting("MACRO_TAG_TEMPLATE")
        l_value = "%" + (tag_template % self.tag) + "%"

        sig_count = db.session.query(yara_rule.Yara_rule) \
            .filter(or_(yara_rule.Yara_rule.strings.like(l_value),
                        yara_rule.Yara_rule.condition.like(l_value))) \
            .count()

        return True if sig_count > 0 else False

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
            entities = db.session.query(Macros).filter(Macros.active > 0).all()
            return [entity.to_dict() for entity in entities]
        except:
            return None
