from app import db


class C2ip(db.Model):
    __tablename__ = "c2ip"

    id = db.Column(db.Integer, primary_key=True)

    date_created = db.Column(db.Date)

    date_modified = db.Column(db.Date)

    ip = db.Column(db.String(15), index=True)

    asn = db.Column(db.String(128))

    country = db.Column(db.String(64))

    city = db.Column(db.String(64))

    state = db.Column(db.String(64))

    reference_link = db.Column(db.String(2048))

    reference_text = db.Column(db.String(2048))

    expiration_type = db.Column(db.String(32))

    expiration_timestamp = db.Column(db.Date)

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            ip=self.ip,
            asn=self.asn,
            country=self.country,
            city=self.city,
            state=self.state,
            reference_link=self.reference_link,
            reference_text=self.reference_text,
            expiration_type=self.expiration_type,
            expiration_timestamp=self.expiration_timestamp.isoformat(),
            id=self.id
        )

    def __repr__(self):
        return '<C2ip %r>' % (self.id)
