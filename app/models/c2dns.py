from app import db
from app.routes import tags_mapping


class C2dns(db.Model):
    __tablename__ = "c2dns"

    id = db.Column(db.Integer, primary_key=True)

    date_created = db.Column(db.Date)

    date_modified = db.Column(db.Date)

    state = db.Column(db.String(32), index=True)

    domain_name = db.Column(db.String(2048), index=True)

    match_type = db.Column(db.Enum('exact', 'wildcard'))

    reference_link = db.Column(db.String(2048))

    reference_text = db.Column(db.String(2048))

    expiration_type = db.Column(db.String(32))

    expiration_timestamp = db.Column(db.Date)

    tags = []

    addedTags = []

    removedTags = []

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            state=self.state,
            domain_name=self.domain_name,
            match_type=self.match_type,
            reference_link=self.reference_link,
            reference_text=self.reference_text,
            expiration_type=self.expiration_type,
            expiration_timestamp=self.expiration_timestamp.isoformat(),
            id=self.id,
            tags=tags_mapping.get_tags_for_source(self.__tablename__, self.id),
            addedTags=[],
            removedTags=[]
        )

    def __repr__(self):
        return '<C2dns %r>' % (self.id)
