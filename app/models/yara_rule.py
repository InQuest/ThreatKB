from app import db, current_user
from app.models.files import Files
from app.routes import tags_mapping
from app.models.comments import Comments
from app.models.cfg_category_range_mapping import CfgCategoryRangeMapping
from app.models import cfg_settings, cfg_states
from sqlalchemy.event import listens_for
from dateutil import parser
import datetime
import json
import distutils

from flask import abort

class Yara_rule(db.Model):

    __tablename__ = "yara_rules"

    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    last_revision_date = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                                   onupdate=db.func.current_timestamp())
    state = db.Column(db.String(32), index=True)
    revision = db.Column(db.Integer(unsigned=True), default=1)
    name = db.Column(db.String(128), index=True)
    test_status = db.Column(db.String(16))
    confidence = db.Column(db.Integer)
    severity = db.Column(db.Integer)
    description = db.Column(db.String(4096))
    category = db.Column(db.String(32), index=True)
    file_type = db.Column(db.String(32))
    subcategory1 = db.Column(db.String(32))
    subcategory2 = db.Column(db.String(32))
    subcategory3 = db.Column(db.String(32))
    reference_link = db.Column(db.String(2048))
    condition = db.Column(db.String(2048))
    strings = db.Column(db.String(30000))
    active = db.Column(db.Boolean, nullable=False, default=True)
    eventid = db.Column(db.Integer(unsigned=True), index=True, nullable=False)

    tags = []
    addedTags = []
    removedTags = []

    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==Yara_rule.created_user_id")

    modified_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    modified_user = db.relationship('KBUser', foreign_keys=modified_user_id,
                                    primaryjoin="KBUser.id==Yara_rule.modified_user_id")

    owner_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=True)
    owner_user = db.relationship('KBUser', foreign_keys=owner_user_id,
                                 primaryjoin="KBUser.id==Yara_rule.owner_user_id")

    comments = db.relationship("Comments", foreign_keys=[id],
                               primaryjoin="and_(Comments.entity_id==Yara_rule.id, Comments.entity_type=='%s')" % (
                                   Comments.ENTITY_MAPPING["SIGNATURE"]), lazy="dynamic", cascade="all,delete")

    files = db.relationship("Files", foreign_keys=[id],
                            primaryjoin="and_(Files.entity_id==Yara_rule.id, Files.entity_type=='%s')" % (
                                Files.ENTITY_MAPPING["SIGNATURE"]), lazy="dynamic", cascade="all,delete")

    history = db.relationship("Yara_rule_history", foreign_keys=[id],
                              primaryjoin="Yara_rule_history.yara_rule_id==Yara_rule.id", lazy="dynamic",
                              cascade="all,delete")

    test_history = db.relationship("Yara_testing_history", foreign_keys=[id],
                                   primaryjoin="Yara_testing_history.yara_rule_id==Yara_rule.id", lazy="dynamic",
                                   cascade="all,delete")

    def to_dict(self):
        revisions = Yara_rule_history.query.filter_by(yara_rule_id=self.id).all()
        comments = Comments.query.filter_by(entity_id=self.id).filter_by(
            entity_type=Comments.ENTITY_MAPPING["SIGNATURE"]).all()
        files = Files.query.filter_by(entity_id=self.id).filter_by(entity_type=Files.ENTITY_MAPPING["SIGNATURE"]).all()
        return dict(
            creationed_date=self.creation_date.isoformat(),
            last_revision_date=self.last_revision_date.isoformat(),
            state=self.state,
            name=self.name,
            test_status=self.test_status,
            confidence=self.confidence,
            severity=self.severity,
            description=self.description,
            category=self.category,
            file_type=self.file_type,
            subcategory1=self.subcategory1,
            subcategory2=self.subcategory2,
            subcategory3=self.subcategory3,
            reference_link=self.reference_link,
            condition="condition:\n\t%s" % self.condition,
            strings="strings:\n\t%s" % self.strings,
            eventid=self.eventid,
            id=self.id,
            tags=tags_mapping.get_tags_for_source(self.__tablename__, self.id),
            addedTags=[],
            removedTags=[],
            comments=[comment.to_dict() for comment in comments],
            revisions=[revision.to_dict() for revision in revisions],
            files=[file.to_dict() for file in files],
            created_user=self.created_user.to_dict(),
            modified_user=self.modified_user.to_dict(),
            owner_user=self.owner_user.to_dict() if self.owner_user else None,
            revision=self.revision
        )

    def to_revision_dict(self):
        dict = self.to_dict()
        del dict["comments"]
        del dict["revisions"]
        del dict["tags"]
        del dict["removedTags"]
        del dict["addedTags"]
        return dict

    def __repr__(self):
        return '<Yara_rule %r>' % (self.id)

    @staticmethod
    def to_yara_rule_string(yara_dict):
        yr = Yara_rule()
        metadata_field_mapping = [attr for attr in dir(yr) if
                                  not callable(getattr(yr, attr)) and not attr.startswith("__")]

        yara_rule_text = "rule %s\n{\n\n" % (yara_dict.get("name"))
        yara_rule_text += "\tmeta:\n"
        for field in metadata_field_mapping:
            if yara_dict.get(field, None):
                yara_rule_text += "\t%s = \"%s\"\n" % (field, yara_dict[field])

        if not "strings:" in yara_dict["strings"]:
            yara_rule_text += "\n\tstrings:\n\t\t%s" % (yara_dict["strings"])
        else:
            yara_rule_text += "\n\t%s" % (yara_dict["strings"])

        if not "condition" in yara_dict["condition"]:
            yara_rule_text += "\n\tcondition:\n\t\t%s\n\n}" % (yara_dict["condition"])
        else:
            yara_rule_text += "\n\t%s\n\n}" % (yara_dict["condition"])

        return yara_rule_text

    @staticmethod
    def make_yara_sane(text, type_):
        type_ = "%s:" if not type_.endswith(":") else type_
        return "\n\t".join([string.strip().strip("\t") for string in text.split("\n") if type_ not in string]).strip()

    @staticmethod
    def get_yara_rule_from_yara_dict(yara_dict, metadata_field_mapping={}):
        clobber_on_import = cfg_settings.Cfg_settings.get_setting("IMPORT_CLOBBER")
        try:
            clobber_on_import = distutils.util.strtobool(clobber_on_import)
        except:
            clobber_on_import = clobber_on_import

        yara_rule = Yara_rule()
        yara_rule.name = yara_dict["rule_name"]

        yara_metadata = {key.lower(): val.strip().strip("\"") for key, val in yara_dict["metadata"].iteritems()}
        for possible_field, mapped_to in metadata_field_mapping.iteritems():
            possible_field = possible_field.lower()
            if possible_field in yara_metadata.keys():
                field = yara_metadata[possible_field] if not mapped_to in ["confidence",
                                                                                                        "severity",
                                                                                "eventid"] else int(
                    yara_metadata[possible_field])

                if mapped_to in ["last_revision_date", "creation_date"]:
                    try:
                        field = parser.parse(field)
                    except:
                        field = datetime.datetime.now()

                ## If the eventid already exists. Skip it.
                if possible_field == "eventid":
                    existing_yara_rule = Yara_rule.query.filter_by(eventid=field).first()
                    if existing_yara_rule:
                        if not clobber_on_import:
                            continue
                        else:
                            db.session.query(Yara_testing_history).filter_by(
                                yara_rule_id=existing_yara_rule.id).delete()
                            db.session.query(Yara_rule_history).filter_by(yara_rule_id=existing_yara_rule.id).delete()
                            db.session.query(Yara_rule).filter_by(id=existing_yara_rule.id).delete()

                setattr(yara_rule, mapped_to, field)

        yara_rule.condition = " ".join(yara_dict["condition_terms"])
        yara_rule.strings = "\n".join(
            ["%s = %s %s" % (r["name"], r["value"], " ".join(r["modifiers"]) if "modifiers" in r else "") for r in
             yara_dict["strings"]])
        if not yara_rule.category:
            yara_rule.category = CfgCategoryRangeMapping.DEFAULT_CATEGORY
        return yara_rule


@listens_for(Yara_rule, "before_insert")
def generate_eventid(mapper, connect, target):
    if not current_user.admin:
        release_state = cfg_states.Cfg_states.query.filter_by(cfg_states.Cfg_states.is_release_state > 0).first()
        if release_state and target.state == release_state.state:
            abort(403)

    if not target.eventid:
        target.eventid = CfgCategoryRangeMapping.get_next_category_eventid(target.category)


@listens_for(Yara_rule, "before_update")
def yara_rule_before_update(mapper, connect, target):
    if not current_user.admin:
        release_state = cfg_states.Cfg_states.query.filter_by(cfg_states.Cfg_states.is_release_state > 0).first()
        if release_state and target.state == release_state.state:
            abort(403)


class Yara_rule_history(db.Model):
    __tablename__ = "yara_rules_history"

    id = db.Column(db.Integer, primary_key=True)

    date_created = db.Column(db.DateTime(timezone=True))
    revision = db.Column(db.Integer(unsigned=True))

    rule_json = db.Column(db.Text, nullable=False)

    yara_rule_id = db.Column(db.Integer, db.ForeignKey("yara_rules.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    user = db.relationship('KBUser', foreign_keys=user_id,
                           primaryjoin="KBUser.id==Yara_rule_history.user_id")

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            revision=self.revision,
            rule_json=json.loads(self.rule_json),
            yara_rule_id=self.yara_rule_id,
            user=self.user.to_dict()
        )

    def __repr__(self):
        return '<Yara_rule_history %r>' % (self.id)


class Yara_testing_history(db.Model):
    __tablename__ = "yara_testing_history"

    id = db.Column(db.Integer, primary_key=True)
    yara_rule_id = db.Column(db.Integer, db.ForeignKey("yara_rules.id"), nullable=False)
    revision = db.Column(db.Integer(unsigned=True), nullable=False)

    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True), nullable=False)
    files_tested = db.Column(db.Integer(unsigned=True), nullable=False)
    files_matched = db.Column(db.Integer(unsigned=True), nullable=False)
    avg_millis_per_file = db.Column(db.Float, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    user = db.relationship('KBUser', foreign_keys=user_id,
                           primaryjoin="KBUser.id==Yara_testing_history.user_id")

    def to_dict(self):
        return dict(
            yara_rule_id=self.yara_rule_id,
            revision=self.revision,
            start_time=self.date_created.isoformat(),
            end_time=self.date_created.isoformat(),
            files_tested=self.files_tested,
            files_matched=self.files_matched,
            user=self.user.to_dict()
        )

    def __repr__(self):
        return '<YaraTestingHistory %r>' % self.id
