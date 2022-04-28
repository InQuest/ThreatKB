from sqlalchemy.event import listens_for

from app import db, ENTITY_MAPPING, ACTIVITY_TYPE
from app.models import activity_log


class Comments(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    comment = db.Column(db.String(65000))
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

    def __repr__(self):
        return '<Comments %r>' % (self.id)


@listens_for(Comments, "after_insert")
def comment_made(mapper, connection, target):
    activity_log.log_activity(connection=connection,
                              activity_type=list(ACTIVITY_TYPE.keys())[list(ACTIVITY_TYPE.keys()).index("COMMENTS")],
                              activity_text=target.comment,
                              activity_text_short=target.comment,
                              activity_date=target.date_created,
                              entity_type=target.entity_type,
                              entity_id=target.entity_id,
                              user_id=target.user_id)
