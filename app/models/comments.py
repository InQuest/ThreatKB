from sqlalchemy.event import listens_for

from app import db, ENTITY_MAPPING, ACTIVITY_TYPE, ENTITY_MAPPING_URI
from app.models import activity_log, yara_rule


class Comments(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    comment = db.Column(db.TEXT())
    entity_type = db.Column(db.Integer(), index=True, nullable=False)
    entity_id = db.Column(db.Integer(), index=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)

    user = db.relationship('KBUser', foreign_keys=user_id)

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            comment=self.comment,
            entity_type=list(ENTITY_MAPPING.keys())[list(ENTITY_MAPPING.values()).index(self.entity_type)],
            entity_id=self.entity_id,
            id=self.id,
            user=self.user.to_dict()
        )

    @staticmethod
    def get_comment_cache():
        mapper = {1: "yara_rules", 2: "c2dns", 3: "c2ip", 4: "tasks"}
        r = {}
        comments = Comments.query.all()
        for comment in comments:
            t = mapper[comment.entity_type]
            if not r.get(t, []):
                r[t] = {}
            if not r[t].get(comment.entity_id, []):
                r[t][comment.entity_id] = []
            r[t][comment.entity_id].append(comment.to_dict())
        return r

    def __repr__(self):
        return '<Comments %r>' % (self.id)


@listens_for(Comments, "after_insert")
def comment_made(mapper, connection, target):
    activity_log.log_activity(connection=connection,
                              activity_type=list(ACTIVITY_TYPE.keys())[list(ACTIVITY_TYPE.keys()).index("COMMENTS")],
                              activity_text=target.comment,
                              activity_date=target.date_created,
                              entity_type=target.entity_type,
                              entity_id=target.entity_id,
                              user_id=target.user_id)
