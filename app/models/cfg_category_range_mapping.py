from app import db


class CfgCategoryRangeMapping(db.Model):
    __tablename__ = "cfg_category_range_mapping"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.String(255), unique=True, nullable=False)
    range_min = db.Column(db.Integer(unsigned=True), index=True, nullable=False)
    range_max = db.Column(db.Integer(unsigned=True), index=True, nullable=False)
    current = db.Column(db.Integer(unsigned=True), index=True, nullable=False)

    def to_dict(self):
        return dict(
            id=self.id,
            category=self.category,
            range_min=self.range_min,
            range_max=self.range_max,
            current=self.current
        )

    def __repr__(self):
        return '<CfgCategoryRangeMapping %r>' % self.id
