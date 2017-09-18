from app import db


class CfgCategoryRangeMapping(db.Model):
    __tablename__ = "cfg_category_range_mapping"

    DEFAULT_CATEGORY = "Uncategorized"
    COMMITTED_DEFAULT = None

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.String(255), unique=True, nullable=False)
    range_min = db.Column(db.Integer(unsigned=True), index=True, nullable=False)
    range_max = db.Column(db.Integer(unsigned=True), index=True, nullable=False)
    current = db.Column(db.Integer(unsigned=True), index=True, nullable=True)

    def to_dict(self):
        return dict(
            id=self.id,
            category=self.category,
            range_min=self.range_min,
            range_max=self.range_max,
            current=self.current
        )

    @staticmethod
    def get_next_category_signature_id(category=None):
        default_category_min = 10000
        default_category_max = 20000

        if not category or not CfgCategoryRangeMapping.query.filter(
                CfgCategoryRangeMapping.category == category).first():
            category = CfgCategoryRangeMapping.query.filter(
                CfgCategoryRangeMapping.category == CfgCategoryRangeMapping.DEFAULT_CATEGORY).first()
            if not category:
                if not CfgCategoryRangeMapping.COMMITTED_DEFAULT:
                    category = CfgCategoryRangeMapping(category=CfgCategoryRangeMapping.DEFAULT_CATEGORY,
                                                       range_max=default_category_max,
                                                       range_min=default_category_min, current=default_category_min)
                    db.session.add(category)
                    CfgCategoryRangeMapping.COMMITTED_DEFAULT = category
                else:
                    category = CfgCategoryRangeMapping.COMMITTED_DEFAULT
            signature_id = category.current + 1
            category.current = signature_id
        else:
            category = CfgCategoryRangeMapping.query.filter(CfgCategoryRangeMapping.category == category).first()
            signature_id = category.current + 1
            category.current = signature_id

        return signature_id


    def __repr__(self):
        return '<CfgCategoryRangeMapping %r>' % self.id
