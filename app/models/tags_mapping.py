from app import db
from app.models import tags_mapping


class Tags_mapping(db.Model):
    __tablename__ = "tags_mapping"

    id = db.Column(db.Integer, primary_key=True)

    source_table = db.Column(db.Enum('c2dns', 'c2ip', 'yara_rules', 'tasks'), index=True)

    source_id = db.Column(db.Integer, index=True)

    tag_id = db.Column(db.Integer, index=True)

    def to_dict(self):
        return dict(
            source_table = self.source_table,
            source_id = self.source_id,
            tag_id = self.tag_id,
            id = self.id
        )

    @staticmethod
    def get_tags_mapping_cache():
        from app.models import tags
        r = {}
        mapping = tags_mapping.Tags_mapping.query.all()
        tags = {tag.id: tag for tag in tags.Tags.query.all()}
        for map in mapping:
            if not r.get(map.source_table, []):
                r[map.source_table] = {}
            if not r[map.source_table].get(map.source_id,[]):
                r[map.source_table][map.source_id] = []
            if map.tag_id in tags:
                r[map.source_table][map.source_id].append(tags[map.tag_id].text)

        return r

    def __repr__(self):
        return '<Tags_mapping %r>' % (self.id)
