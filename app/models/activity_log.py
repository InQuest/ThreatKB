from sqlalchemy.orm import class_mapper

from app import db, ENTITY_MAPPING, ACTIVITY_TYPE, ENTITY_MAPPING_URI, app
from sqlalchemy import bindparam, inspect

from app.models import users, cfg_settings, users
from app.models.cfg_states import Cfg_states
import re
from flask import request

from app.slack_helper import SlackHelper

class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_type = db.Column(db.String(256))
    activity_text = db.Column(db.TEXT())
    activity_text_short = db.Column(db.String(1000))
    activity_date = db.Column(db.DateTime(timezone=True))

    entity_type = db.Column(db.Integer(unsigned=True), index=True, nullable=False)
    entity_id = db.Column(db.Integer(unsigned=True), index=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=True)
    user = db.relationship('KBUser', foreign_keys=user_id)

    def to_dict(self):
        return dict(
            id=self.id,
            activity_type=ACTIVITY_TYPE.values()[ACTIVITY_TYPE.keys().index(self.activity_type)],
            activity_text=self.activity_text,
            activity_date=self.activity_date.isoformat(),
            entity_type=ENTITY_MAPPING.keys()[ENTITY_MAPPING.values().index(self.entity_type)],
            entity_id=self.entity_id,
            user=self.user.to_dict()
        )


def get_modified_changes(target):
    """
    Get list of modified changes.
    :param target: target
    :return: list of modified changes
    """
    inspection = inspect(target)
    attrs = class_mapper(target.__class__).column_attrs

    changes = {"short": [], "long": []}
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
                changes["long"].append("'%s' changed from '%s' to '%s'" % (attr.key, before, after))
                changes["short"].append("'%s'" % (attr.key))

    changes["long"] = [re.sub("[^\x00-\x7F]", "", change) for change in changes["long"]]
    changes["short"] = [re.sub("[^\x00-\x7F]", "", change) for change in changes["short"]]
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
                 user_id,
                 activity_text_short=""):
    transaction = connection.begin()

    webhook = cfg_settings.Cfg_settings.get_setting(key="SLACK_WEBHOOK")

    if webhook:
        post_when = cfg_settings.Cfg_settings.get_setting(key="SLACK_POST_WHEN")
        post_when = post_when.split(",") if post_when else []
        exclude_users = cfg_settings.Cfg_settings.get_setting(key="SLACK_EXCLUDE_USERS")
        exclude_users = exclude_users.split(",") if exclude_users else []
        channel = cfg_settings.Cfg_settings.get_setting(key="SLACK_CHANNEL")
        slack_user = cfg_settings.Cfg_settings.get_setting(key="SLACK_USER")
        template = cfg_settings.Cfg_settings.get_setting(key="SLACK_TEMPLATE")

        if activity_type in post_when and webhook and slack_user and channel:
            user = db.session.query(users.KBUser).filter(users.KBUser.id == user_id).first()
            if user.email in exclude_users:
                app.logger.debug("Skipping slack because user %s in exclude list %s" % (user.email, exclude_users))
                return
            url = "%s#!/%s/%s" % (request.url_root, ENTITY_MAPPING_URI[int(entity_type)], entity_id)

            from app.models import yara_rule, c2dns, c2ip, tasks, releases
            ENTITY_MAPPING_MODEL = {1: yara_rule.Yara_rule, 2: c2dns.C2dns, 3: c2ip.C2ip, 4: tasks.Tasks,
                                    5: releases.Release}
            name_mapping = {yara_rule.Yara_rule: "name", c2ip.C2ip: "ip", c2dns.C2dns: "domain_name",
                            tasks.Tasks: "title", releases.Release: "name"}
            model = ENTITY_MAPPING_MODEL[int(entity_type)]
            entity = db.session.query(model).filter(model.id == entity_id).first()
            try:
                entity_name = getattr(entity, name_mapping[model])
            except:
                entity_name = "NA"

            template = template.replace("USER_EMAIL", user.email)
            template = template.replace("USER_ID", str(user.id))
            template = template.replace("USER_FIRSTNAME", user.first_name)
            template = template.replace("USER_LASTNAME", user.last_name)
            template = template.replace("URL", url)
            template = template.replace("ACTIVITY_TYPE", activity_type)
            template = template.replace("ACTIVITY_TEXT_SHORT", activity_text_short)
            template = template.replace("ACTIVITY_TEXT", activity_text)
            template = template.replace("ACTIVITY_DATE", str(activity_date))
            template = template.replace("ENTITY_TYPE", ENTITY_MAPPING_URI[int(entity_type)])
            template = template.replace("ENTITY_ID", str(entity_id))
            template = template.replace("ENTITY_NAME", str(entity_name))
            SlackHelper.send_slack_message(webhook, slack_user, channel, template)

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
