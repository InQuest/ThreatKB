from app import db
import yara_rule


class CfgCategoryRangeMapping(db.Model):
    __tablename__ = "cfg_category_range_mapping"

    DEFAULT_CATEGORY = "Uncategorized"
    COMMITTED_DEFAULT = None

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.String(255), unique=True, nullable=False)
    range_min = db.Column(db.Integer(unsigned=True), index=True, nullable=False)
    range_max = db.Column(db.Integer(unsigned=True), index=True, nullable=False)
    current = db.Column(db.Integer(unsigned=True), index=True, nullable=True)
    include_in_release_notes = db.Column(db.Boolean, nullable=False, default=True, index=True)

    def to_dict(self, include_inactive=False):

        if include_inactive:
            sig_count = db.session.query(yara_rule.Yara_rule).filter(yara_rule.Yara_rule.eventid >= self.range_min,
                                                                     yara_rule.Yara_rule.eventid <= self.range_max).count()
        else:
            sig_count = db.session.query(yara_rule.Yara_rule) \
                .filter(yara_rule.Yara_rule.eventid >= self.range_min, yara_rule.Yara_rule.eventid <= self.range_max) \
                .filter(yara_rule.Yara_rule.active > 0).count()

        return dict(
            id=self.id,
            category=self.category,
            range_min=self.range_min,
            range_max=self.range_max,
            current=self.current,
            sig_count=sig_count,
            include_in_release_notes=self.include_in_release_notes
        )

    @staticmethod
    def get_next_category_eventid(category=None):
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
                    CfgCategoryRangeMapping.COMMITTED_DEFAULT = category
                else:
                    category = CfgCategoryRangeMapping.COMMITTED_DEFAULT
            eventid = category.current + 1

            ## Make sure its not already taken by an imported signature
            while yara_rule.Yara_rule.query.filter_by(eventid=eventid).first():
                eventid = eventid + 1
            category.current = eventid
        else:
            category = CfgCategoryRangeMapping.query.filter(CfgCategoryRangeMapping.category == category).first()
            eventid = category.current + 1
            category.current = eventid

        db.session.execute(
            "update `cfg_category_range_mapping` set current=%s where id=%s" % (category.current, category.id))
        return eventid


    def __repr__(self):
        return '<CfgCategoryRangeMapping %r>' % self.id
