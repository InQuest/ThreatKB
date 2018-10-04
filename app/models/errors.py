from app import db


class Error(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    stacktrace = db.Column(db.TEXT)
    route = db.Column(db.String(1024))
    method = db.Column(db.String(16))
    remote_addr = db.Column(db.String(32))
    args = db.Column(db.TEXT)

    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)

    user = db.relationship('KBUser', foreign_keys=user_id)

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            stacktrace=self.stacktrace,
            id=self.id,
            user=self.user.to_dict(),
            route=self.route,
            method=self.method,
            remote_addr=self.remote_addr,
            args=self.args
        )

    def __repr__(self):
        return '<Error %r %s>' % (self.id, self.route)
