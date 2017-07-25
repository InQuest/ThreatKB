from app import db


class Cfg_states(db.Model):
    __tablename__ = "cfg_states"

    id = db.Column(db.Integer, primary_key=True)

    state = db.Column(db.String(32))

    def to_dict(self):
        return dict(
            state=self.state,
            id=self.id
        )

    def __repr__(self):
        return '<Cfg_states %r>' % (self.id)
