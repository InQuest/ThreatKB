from app import db


class Cfg_reference_text_templates(db.Model):
    __tablename__ = "cfg_reference_text_templates"

    id = db.Column(db.Integer, primary_key=True)

    template_text = db.Column(db.String(2048))

    def to_dict(self):
        return dict(
            template_text=self.template_text,
            id=self.id
        )

    def __repr__(self):
        return '<Cfg_reference_text_templates %r>' % (self.id)
