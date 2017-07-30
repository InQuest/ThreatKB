import datetime
from app import db, bcrypt


class KBUser(db.Model):
    __tablename__ = "kb_users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    admin = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, email, password, admin=False):
        self.email = email
        self.password = bcrypt.generate_password_hash(password)
        self.admin = admin

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User {0}>'.format(self.email)

    def to_dict(self):
        return dict(
            email=self.email,
            registered_on=self.registered_on.isoformat(),
            id=self.id
        )
