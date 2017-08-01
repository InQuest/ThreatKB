from app import db


class Tags_mapping(db.Model):
    __tablename__ = "tags_mapping"

    id = db.Column(db.Integer, primary_key=True)

    source_table = db.Column(db.Enum('c2dns', 'c2ip', 'yara_rule'), index=True)

    source_id = db.Column(db.Integer, index=True)

    tag_id = db.Column(db.Integer, index=True)

    def to_dict(self):
        return dict(
            source_table = self.source_table,
            source_id = self.source_id,
            tag_id = self.tag_id,
            id = self.id
        )

    def __repr__(self):
        return '<Tags_mapping %r>' % (self.id)
