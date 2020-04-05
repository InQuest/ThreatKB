from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session

from app import db, ENTITY_MAPPING, ACTIVITY_TYPE
from app.models import activity_log
from app.models.comments import Comments


class Tasks(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    state = db.Column(db.String(32), index=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    title = db.Column(db.String(256), index=True)
    description = db.Column(db.String(2048), index=True)
    final_artifact = db.Column(db.String(4096))

    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==Tasks.created_user_id")

    modified_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    modified_user = db.relationship('KBUser', foreign_keys=modified_user_id,
                                    primaryjoin="KBUser.id==Tasks.modified_user_id")

    owner_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=True)
    owner_user = db.relationship('KBUser', foreign_keys=owner_user_id,
                                 primaryjoin="KBUser.id==Tasks.owner_user_id")

    comments = db.relationship("Comments", foreign_keys=[id],
                               primaryjoin="and_(Comments.entity_id==Tasks.id, Comments.entity_type=='%s')" % (
                                   ENTITY_MAPPING["DNS"]))

    def to_dict(self, include_comments=True):
        task = dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            state=self.state,
            title=self.title,
            description=self.description,
            final_artifact=self.final_artifact,
            id=self.id,
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict(),
            owner_user=self.owner_user.to_dict() if self.owner_user else None
        )

        if include_comments:
            task["comments"] = [comment.to_dict() for comment in Comments.query.filter_by(entity_id=self.id).filter_by(
                entity_type=ENTITY_MAPPING["TASK"]).all()]

        return task

    def __repr__(self):
        return '<Tasks %r>' % self.id


@listens_for(Tasks, "after_insert")
def task_created(mapper, connection, target):
    activity_log.log_activity(connection=connection,
                              activity_type=ACTIVITY_TYPE.keys()[ACTIVITY_TYPE.keys().index("ARTIFACT_CREATED")],
                              activity_text=target.title,
                              activity_date=target.date_created,
                              entity_type=ENTITY_MAPPING["TASK"],
                              entity_id=target.id,
                              user_id=target.created_user_id)


@listens_for(Tasks, "after_update")
def task_modified(mapper, connection, target):
    session = Session.object_session(target)

    if session.is_modified(target, include_collections=False):
        state_activity_text = activity_log.get_state_change(target, target.title)
        if state_activity_text:
            activity_log.log_activity(connection=connection,
                                      activity_type=ACTIVITY_TYPE.keys()[ACTIVITY_TYPE.keys().index("STATE_TOGGLED")],
                                      activity_text=state_activity_text,
                                      activity_date=target.date_modified,
                                      entity_type=ENTITY_MAPPING["TASK"],
                                      entity_id=target.id,
                                      user_id=target.modified_user_id)

        changes = activity_log.get_modified_changes(target)
        if changes["long"].__len__() > 0:
            activity_log.log_activity(connection=connection,
                                      activity_type=ACTIVITY_TYPE.keys()[ACTIVITY_TYPE.keys().index("ARTIFACT_MODIFIED")],
                                      activity_text="'%s' modified with changes: %s"
                                                    % (target.title, ', '.join(map(str, changes["long"]))),
                                      activity_text_short="'%s' modified fields are: %s"
                                                    % (target.title, ', '.join(map(str, changes["short"]))),
                                      activity_date=target.date_modified,
                                      entity_type=ENTITY_MAPPING["TASK"],
                                      entity_id=target.id,
                                      user_id=target.modified_user_id)
