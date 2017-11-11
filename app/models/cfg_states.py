from app import db
from sqlalchemy.event import listens_for


class Cfg_states(db.Model):
    __tablename__ = "cfg_states"

    id = db.Column(db.Integer, primary_key=True)

    state = db.Column(db.String(32))
    is_release_state = db.Column(db.Integer, default=0)

    def to_dict(self):
        from app.models import yara_rule, c2dns, c2ip, tasks
        return dict(
            state=self.state,
            id=self.id,
            is_release_state=self.is_release_state,
            sig_count=db.session.query(yara_rule.Yara_rule).filter(yara_rule.Yara_rule.state == self.state).count(),
            dns_count=db.session.query(c2dns.C2dns).filter(c2dns.C2dns.state == self.state).count(),
            ip_count=db.session.query(c2ip.C2ip).filter(c2ip.C2ip.state == self.state).count(),
            task_count=db.session.query(tasks.Tasks).filter(tasks.Tasks.state == self.state).count(),
        )

    def __repr__(self):
        return '<Cfg_states %r>' % self.id


def verify_state(state_to_verify):
    cfg_state = Cfg_states.query.filter(Cfg_states.state == state_to_verify).first()
    if not cfg_state:
        entity = Cfg_states(
            state=state_to_verify,
            is_release_state=0
        )
        db.session.add(entity)
        db.session.commit()

    return state_to_verify


@listens_for(Cfg_states, "before_insert")
def generate_eventid(mapper, connect, target):
    if target.is_release_state > 0:
        Cfg_states.query.update(dict(is_release_state=0))


@listens_for(Cfg_states, "before_update")
def generate_eventid(mapper, connect, target):
    if target.is_release_state > 0:
        Cfg_states.query.filter(Cfg_states.id != target.id).update(dict(is_release_state=0))
