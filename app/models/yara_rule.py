from app import db


class Yara_rule(db.Model):
    __tablename__ = "yara_rules"

    id = db.Column(db.Integer, primary_key=True)

    date_created = db.Column(db.Date)

    date_modified = db.Column(db.Date)

    state = db.Column(db.String(32), index=True)

    name = db.Column(db.String(128), index=True)

    test_status = db.Column(db.String(16))

    confidence = db.Column(db.Integer)

    severity = db.Column(db.Integer)

    description = db.Column(db.String(4096))

    category = db.Column(db.String(32))

    file_type = db.Column(db.String(32))

    subcategory1 = db.Column(db.String(32))

    subcategory2 = db.Column(db.String(32))

    subcategory3 = db.Column(db.String(32))

    reference_link = db.Column(db.String(2048))

    reference_text = db.Column(db.String(2048))

    condition = db.Column(db.String(2048))

    strings = db.Column(db.String(30000))

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            state=self.state,
            name=self.name,
            test_status=self.test_status,
            confidence=self.confidence,
            severity=self.severity,
            description=self.description,
            category=self.category,
            file_type=self.file_type,
            subcategory1=self.subcategory1,
            subcategory2=self.subcategory2,
            subcategory3=self.subcategory3,
            reference_link=self.reference_link,
            reference_text=self.reference_text,
            condition=self.condition,
            strings=self.strings,
            id=self.id
        )

    def __repr__(self):
        return '<Yara_rule %r>' % (self.id)
