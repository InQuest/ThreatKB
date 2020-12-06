from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app import db
from app.models import users


class Tags_mapping(db.Model):
    __tablename__ = "tags_mapping"

    id = db.Column(db.Integer, primary_key=True)

    source_table = db.Column(db.Enum('c2dns', 'c2ip', 'yara_rules', 'tasks'), index=True)

    source_id = db.Column(db.Integer, index=True)

    tag_id = db.Column(db.Integer, index=True)

    creation_date = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())

    created_user_id = db.Column(db.Integer)

    @property
    def created_user(self):
        return db.session.query(users.KBUser).filter(
            users.KBUser.id == self.created_user_id).first() if self.created_user_id else None

    def to_dict(self):
        return dict(
            source_table = self.source_table,
            source_id = self.source_id,
            tag_id = self.tag_id,
            id=self.id,
            creation_date=self.creation_date.isoformat() if self.creation_date else None,
            created_user=self.created_user.to_dict() if self.created_user else {}
        )

    def __repr__(self):
        return '<Tags_mapping %r>' % (self.id)


@listens_for(Tags_mapping, "before_insert")
def tag_created(mapper, connection, target):
    from app.models import activity_log, yara_rule, tasks, c2dns, c2ip, tags
    from app import ENTITY_MAPPING, ACTIVITY_TYPE, db
    from datetime import datetime

    if target.source_table == "yara_rules":
        entity = db.session.query(yara_rule.Yara_rule).filter(yara_rule.Yara_rule.id == target.source_id).one()
        name = entity.name
        entity_type = ENTITY_MAPPING["SIGNATURE"]
    elif target.source_table == "c2dns":
        entity = db.session.query(c2dns.C2dns).filter(c2dns.C2dns.id == target.source_id).one()
        name = entity.domain_name
        entity_type = ENTITY_MAPPING["DNS"]
    elif target.source_table == "c2ip":
        entity = db.session.query(c2ip.C2ip).filter(c2ip.C2ip.id == target.source_id).one()
        name = entity.ip
        entity_type = ENTITY_MAPPING["IP"]
    else:
        entity = db.session.query(tasks.Tasks).filter(tasks.Tasks.id == target.source_id).one()
        name = entity.title
        entity_type = ENTITY_MAPPING["TASK"]

    tag = db.session.query(tags.Tags).filter(tags.Tags.id == target.tag_id).one()

    if entity and tag:
        activity_text = "%s '%s' assigned tag '%s'" % (target.source_table.title(), name, tag.text)
        activity_log.log_activity(connection=connection,
                                  activity_type=ACTIVITY_TYPE.keys()[ACTIVITY_TYPE.keys().index("TAG_CREATED")],
                                  activity_text=activity_text,
                                  activity_date=datetime.now(),
                                  entity_type=entity_type,
                                  entity_id=entity.id,
                                  user_id=target.created_user_id or None)


@listens_for(Tags_mapping, "after_delete")
def tag_modified(mapper, connection, target):
    from app.models import activity_log, yara_rule, tasks, c2dns, c2ip, tags
    from app import ENTITY_MAPPING, ACTIVITY_TYPE, db
    from datetime import datetime

    session = Session.object_session(target)

    if target.source_table == "yara_rules":
        entity = db.session.query(yara_rule.Yara_rule).filter(yara_rule.Yara_rule.id == target.source_id).one()
        name = entity.name
        entity_type = ENTITY_MAPPING["SIGNATURE"]
    elif target.source_table == "c2dns":
        entity = db.session.query(c2dns.C2dns).filter(c2dns.C2dns.id == target.source_id).one()
        name = entity.domain_name
        entity_type = ENTITY_MAPPING["DNS"]
    elif target.source_table == "c2ip":
        entity = db.session.query(c2ip.C2ip).filter(c2ip.C2ip.id == target.source_id).one()
        name = entity.ip
        entity_type = ENTITY_MAPPING["IP"]
    else:
        entity = db.session.query(tasks.Tasks).filter(tasks.Tasks.id == target.source_id).one()
        name = entity.title
        entity_type = ENTITY_MAPPING["TASK"]

    tag = db.session.query(tags.Tags).filter(tags.Tags.id == target.tag_id).one()

    if entity and tag:
        activity_text = "Tag '%s' removed from %s '%s' " % (tag.text, target.source_table.title(), name)
        activity_log.log_activity(connection=connection,
                                  activity_type=ACTIVITY_TYPE.keys()[ACTIVITY_TYPE.keys().index("TAG_REMOVED")],
                                  activity_text=activity_text,
                                  activity_date=datetime.now(),
                                  entity_type=entity_type,
                                  entity_id=entity.id,
                                  user_id=target.created_user_id or None)
