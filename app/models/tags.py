from app import db
from app.models import users

class Tags(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key = True)
    
    text = db.Column(db.String(256))
    creation_date = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    created_user_id = db.Column(db.Integer)

    @property
    def created_user(self):
        return db.session.query(users.KBUser).filter(
            users.KBUser.id == self.created_user_id).first() if self.created_user_id else None

    def to_dict(self):
        return dict(
            text = self.text,
            id=self.id,
            creation_date=self.creation_date.isoformat() if self.creation_date else None,
            created_user=self.created_user.to_dict() if self.created_user else {}
        )

    def __repr__(self):
        return '<Tags %r>' % (self.id)

