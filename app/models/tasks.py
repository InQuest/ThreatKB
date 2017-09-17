from app import db
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
                                   Comments.ENTITY_MAPPING["DNS"]), lazy="dynamic")

    def to_dict(self):
        comments = Comments.query.filter_by(entity_id=self.id).filter_by(
            entity_type=Comments.ENTITY_MAPPING["TASK"]).all()
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            state=self.state,
            title=self.title,
            description=self.description,
            final_artifact=self.final_artifact,
            id=self.id,
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict(),
            owner_user=self.owner_user.to_dict() if self.owner_user else None,
            comments=[comment.to_dict() for comment in comments]
        )

    def __repr__(self):
        return '<Tasks %r>' % (self.id)
