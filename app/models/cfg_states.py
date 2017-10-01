from app import db
from sqlalchemy.event import listens_for

class Cfg_states(db.Model):
    __tablename__ = "cfg_states"

    id = db.Column(db.Integer, primary_key=True)

    state = db.Column(db.String(32))
    is_release_state = db.Column(db.Integer, default=0)

    def to_dict(self):
        return dict(
            state=self.state,
            id=self.id,
            is_release_state=self.is_release_state
        )

    def __repr__(self):
        return '<Cfg_states %r>' % (self.id)


@listens_for(Cfg_states, "before_insert")
def generate_eventid(mapper, connect, target):
    if target.is_release_state > 0:
        Cfg_states.query.update(dict(is_release_state=0))


@listens_for(Cfg_states, "before_update")
def generate_eventid(mapper, connect, target):
    if target.is_release_state > 0:
        Cfg_states.query.filter(Cfg_states.id != target.id).update(dict(is_release_state=0))
