from sqlalchemy.orm import class_mapper

from app import db, ENTITY_MAPPING, ACTIVITY_TYPE
from sqlalchemy import bindparam, inspect

from app.models import users
from app.models.cfg_states import Cfg_states
import re

class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_type = db.Column(db.String(256))
    activity_text = db.Column(db.String(65000))
    activity_date = db.Column(db.DateTime(timezone=True))

    entity_type = db.Column(db.Integer(), index=True, nullable=False)
    entity_id = db.Column(db.Integer(), index=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=True)
    user = db.relationship('KBUser', foreign_keys=user_id)

    def to_dict(self):
        return dict(
            id=self.id,
            activity_type=list(ACTIVITY_TYPE.values())[list(ACTIVITY_TYPE.keys()).index(self.activity_type)],
            activity_text=self.activity_text,
            activity_date=self.activity_date.isoformat(),
            entity_type=list(ENTITY_MAPPING.keys())[list(ENTITY_MAPPING.values()).index(self.entity_type)],
            entity_id=self.entity_id,
            user=self.user.to_dict() if self.user else {}
        )


def get_modified_changes(target):
    """
    Get list of modified changes.
    :param target: target
    :return: list of modified changes
    """
    inspection = inspect(target)
    attrs = class_mapper(target.__class__).column_attrs

    changes = []
    for attr in attrs:
        attr_hist = getattr(inspection.attrs, attr.key).history
        if attr_hist.has_changes():
            if "user_id" in attr.key:
                before = attr_hist.deleted[0][0] if isinstance(attr_hist.deleted[0], tuple) else attr_hist.deleted[0]
                after = attr_hist.added[0][0] if isinstance(attr_hist.added[0], tuple) else attr_hist.added[0]

                before = users.KBUser.query.get(int(before)).email if before is not None else None
                after = users.KBUser.query.get(int(after)).email if after is not None else None
            else:
                before = attr_hist.deleted[0]
                after = attr_hist.added[0]

            if before != after:
                changes.append("'%s' changed from '%s' to '%s'" % (attr.key, before, after))

    changes = [re.sub("[^\x00-\x7F]", "", change) for change in changes]
    return changes


def get_state_change(target, artifact):
    """
    Get state change.
    :param target: target
    :return: activity text if state is toggled, else None
    """
    activity_text = None

    inspection = inspect(target)
    attrs = class_mapper(target.__class__).column_attrs

    if hasattr(attrs, "state"):
        state_history = getattr(inspection.attrs, "state").history
        if state_history.has_changes():
            o_state = Cfg_states.query.filter(Cfg_states.state == state_history.deleted[0]).first()
            n_state = Cfg_states.query.filter(Cfg_states.state == state_history.added[0]).first()

            if o_state.is_release_state > 0 or o_state.is_retired_state > 0 or o_state.is_staging_state > 0\
                    or n_state.is_release_state > 0 or n_state.is_retired_state > 0 or n_state.is_staging_state > 0:
                activity_text = "State for '%s' was toggled from '%s' to '%s'" \
                                % (artifact, o_state.state, n_state.state)

    return activity_text


def log_activity(connection,
                 activity_type,
                 activity_text,
                 activity_date,
                 entity_type,
                 entity_id,
                 user_id):
    transaction = connection.begin()
    connection.execute(ActivityLog.__table__.insert().values(
        activity_type=bindparam("activity_type"),
        activity_text=bindparam("activity_text"),
        activity_date=bindparam("activity_date"),
        entity_type=bindparam("entity_type"),
        entity_id=bindparam("entity_id"),
        user_id=bindparam("user_id")
    ), {
        "activity_type": activity_type,
        "activity_text": activity_text,
        "activity_date": activity_date,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user_id
    })
    transaction.commit()
