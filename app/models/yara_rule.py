from app import db, current_user, ENTITY_MAPPING
from app.models.files import Files
from app.routes import tags_mapping
from app.models.comments import Comments
from app.models.metadata import MetadataMapping, Metadata
from app.models.cfg_category_range_mapping import CfgCategoryRangeMapping
from app.models import cfg_settings, cfg_states
from sqlalchemy.event import listens_for
from dateutil import parser
import datetime
import json
import re
import distutils
import zlib

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
    category = db.Column(db.String(32), index=True)
    condition = db.Column(db.String(2048))
    strings = db.Column(db.String(30000))
    imports = db.Column(db.String(512))
    description = db.Column(db.TEXT())
    references = db.Column(db.TEXT())
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
                                   ENTITY_MAPPING["SIGNATURE"]), lazy="dynamic", cascade="all,delete")

    files = db.relationship("Files", foreign_keys=[id],
                            primaryjoin="and_(Files.entity_id==Yara_rule.id, Files.entity_type=='%s')" % (
                                ENTITY_MAPPING["SIGNATURE"]), lazy="dynamic", cascade="all,delete")

    history = db.relationship("Yara_rule_history", foreign_keys=[id],
                              primaryjoin="Yara_rule_history.yara_rule_id==Yara_rule.id", lazy="dynamic",
                              cascade="all,delete")

    test_history = db.relationship("Yara_testing_history", foreign_keys=[id],
                                   primaryjoin="Yara_testing_history.yara_rule_id==Yara_rule.id", lazy="dynamic",
                                   cascade="all,delete")

    @property
    def metadata_fields(self):
        return db.session.query(Metadata).filter(Metadata.artifact_type == ENTITY_MAPPING["SIGNATURE"]).all()

    @property
    def metadata_values(self):
        return db.session.query(MetadataMapping) \
            .join(Metadata, Metadata.id == MetadataMapping.metadata_id) \
            .filter(Metadata.active > 0) \
            .filter(Metadata.artifact_type == ENTITY_MAPPING["SIGNATURE"]) \
            .filter(MetadataMapping.artifact_id == self.id) \
            .all()

    def to_dict(self, include_yara_rule_string=None, short=False, include_relationships=True):
        metadata_values_dict = {}
        metadata_keys = Metadata.get_metadata_keys("SIGNATURE")
        metadata_values_dict = {m["metadata"]["key"]: m for m in [entity.to_dict() for entity in self.metadata_values]}
        for key in list(set(metadata_keys) - set(metadata_values_dict.keys())):
            metadata_values_dict[key] = {}

        yara_dict = dict(
            creation_date=self.creation_date.isoformat() if self.creation_date else None,
            last_revision_date=self.last_revision_date.isoformat() if self.last_revision_date else None,
            state=self.state,
            name=self.name,
            category=self.category,
            eventid=self.eventid,
            id=self.id,
            tags=tags_mapping.get_tags_for_source(self.__tablename__, self.id),
            addedTags=[],
            description=self.description,
            references=self.references,
            removedTags=[],
            revision=self.revision,
            metadata=Metadata.get_metadata_dict("SIGNATURE"),
            metadata_values=metadata_values_dict,
            condition="condition:\n\t%s" % self.condition,
            strings="strings:\n\t%s" % self.strings if self.strings and self.strings.strip() else "",
            imports=self.imports
        )

        if include_relationships:
            yara_dict["created_user"] = self.created_user.to_dict()
            yara_dict["modified_user"] = self.modified_user.to_dict()
            yara_dict["owner_user"] = self.owner_user.to_dict() if self.owner_user else None

        if not short:
            revisions = Yara_rule_history.query.filter_by(yara_rule_id=self.id).all()
            comments = Comments.query.filter_by(entity_id=self.id).filter_by(
                entity_type=ENTITY_MAPPING["SIGNATURE"]).all()
            files = Files.query.filter_by(entity_id=self.id).filter_by(entity_type=ENTITY_MAPPING["SIGNATURE"]).all()
            yara_dict.update(dict(comments=[comment.to_dict() for comment in comments],
                                  revisions=[revision.to_dict() for revision in revisions],
                                  files=[file.to_dict() for file in files],
                                  ))

        if include_yara_rule_string:
            yara_dict["yara_rule_string"] = Yara_rule.to_yara_rule_string(yara_dict)

        return yara_dict

    def to_revision_dict(self):
        dict = self.to_dict()
        del dict["comments"]
        del dict["revisions"]
        del dict["tags"]
        del dict["removedTags"]
        del dict["addedTags"]
        return dict

    def to_release_dict(self, metadata_cache, user_cache):
        return dict(
            creation_date=self.creation_date.isoformat(),
            last_revision_date=self.last_revision_date.isoformat(),
            state=self.state,
            name=self.name,
            category=self.category,
            eventid=self.eventid,
            id=self.id,
            description=self.description,
            references=self.references,
            addedTags=[],
            removedTags=[],
            created_user=user_cache[self.created_user_id],
            modified_user=user_cache[self.modified_user_id],
            owner_user=user_cache[self.owner_user_id] if self.owner_user_id else None,
            revision=self.revision,
            metadata=metadata_cache["SIGNATURE"][self.id]["metadata"] if metadata_cache["SIGNATURE"].get(self.id,
                                                                                                         None) and
                                                                         metadata_cache["SIGNATURE"][self.id].get(
                                                                             "metadata", None) else {},
            metadata_values=metadata_cache["SIGNATURE"][self.id]["metadata_values"] if metadata_cache["SIGNATURE"].get(
                self.id, None) and metadata_cache["SIGNATURE"][self.id].get("metadata_values", None) else {},
            condition="condition:\n\t%s" % self.condition,
            strings="strings:\n\t%s" % self.strings if self.strings and self.strings.strip() else "",
            imports=self.imports
        )

    def __repr__(self):
        return '<Yara_rule %r>' % (self.id)

    @staticmethod
    def get_imports_from_string(imports_string):
        if not imports_string:
            return ""
        return "\n".join([imp.strip() for imp in
                          set(re.findall(r'^import[\t\s]+\"[A-Za-z0-9_]+\"[\t\s]*$', imports_string, re.MULTILINE))])

    @staticmethod
    def to_yara_rule_string(yara_dict, include_imports=True):
        yr = Yara_rule()
        metadata_field_mapping = [attr for attr in dir(yr) if
                                  not callable(getattr(yr, attr)) and not attr.startswith("__")]

        yara_rule_text = ""

        if yara_dict.get("imports", None) and include_imports:
            yara_rule_text = yara_dict.get("imports") + "\n\n"

        yara_rule_text += "rule %s\n{\n\n" % (yara_dict.get("name"))
        yara_rule_text += "\tmeta:\n"
        metadata_strings = []
        for field in metadata_field_mapping:
            if yara_dict.get(field, None) and not "metadata" in field and field in ["creation_date",
                                                                                    "last_revision_date", "revision",
                                                                                    "name", "category", "eventid",
                                                                                    "description"]:
                metadata_strings.append("\t\t%s = \"%s\"\n" % (
                    field.title() if not field.lower() == "eventid" else "EventID",
                    str(yara_dict[field]).replace("\"", "'")))

        try:
            for type_, metalist in yara_dict["metadata"].iteritems():
                for meta in metalist:
                    if meta["export_with_release"]:
                        value = yara_dict["metadata_values"][meta["key"]]["value"] if "value" in \
                                                                                      yara_dict["metadata_values"][
                                                                                          meta["key"]] else "NA"
                        metadata_strings.append("\t\t%s = \"%s\"\n" % (meta["key"], str(value).replace("\"", "'")))
        except Exception as e:
            pass

        yara_rule_text += "".join(sorted(metadata_strings))
        formatted_strings = ""

        if yara_dict["strings"] and yara_dict["strings"].strip() and not "strings:" in yara_dict["strings"]:
            formatted_strings = "\n\tstrings:\n\t\t"
            formatted_strings += "\n\t\t".join([line.strip() for line in yara_dict["strings"].split("\n")])
            # yara_rule_text += "\n\tstrings:\n\t\t%s" % (yara_dict["strings"])
        else:
            if not yara_dict["strings"] or not yara_dict["strings"].strip():
                formatted_strings += ""
            else:
                formatted_strings = "\n\tstrings:\n\t\t"
                formatted_strings += "\n\t\t".join([line.strip() for line in yara_dict["strings"].split("\n")[1:]])
                # yara_rule_text += "\n\t%s" % (yara_dict["strings"])

        yara_rule_text += formatted_strings
        formatted_condition = ""

        if not "condition" in yara_dict["condition"]:
            formatted_condition = "\n\tstrings:\n\t\t"
            formatted_condition += "\n\t\t".join([line.strip() for line in yara_dict["condition"].split("\n")])
            #yara_rule_text += "\n\tcondition:\n\t\t%s\n\n}" % (yara_dict["condition"])
        else:
            formatted_condition = "\n\tcondition:\n\t\t"
            formatted_condition += "\n\t\t".join([line.strip() for line in yara_dict["condition"].split("\n")[1:]])
            # yara_rule_text += "\n\t%s\n\n}" % (yara_dict["condition"])

        yara_rule_text += formatted_condition + "\n}\n"

        return yara_rule_text.encode("utf-8")

    @staticmethod
    def make_yara_sane(text, type_):
        if not text or not text.strip() or not text.strip("\t"):
            return ""

        type_ = "%s:" if not type_.endswith(":") else type_
        return "\n\t".join([string.strip().strip("\t") for string in text.split("\n") if type_ not in string]).strip()

    @classmethod
    def get_yara_rule_from_yara_dict(cls, yara_dict, metadata_field_mapping={}):
        condition = yara_dict["condition"]
        strings = yara_dict["strings"]
        imports = yara_dict["imports"]
        yara_dict = yara_dict["rule"]

        metadata_fields = {entity.key.lower(): entity for entity in
                           db.session.query(Metadata).filter(Metadata.active > 0).filter(
                               Metadata.artifact_type == ENTITY_MAPPING["SIGNATURE"]).all()}
        fields_to_add = []

        clobber_on_import = cfg_settings.Cfg_settings.get_setting("IMPORT_CLOBBER")
        try:
            clobber_on_import = distutils.util.strtobool(clobber_on_import)
        except:
            clobber_on_import = clobber_on_import

        yara_rule = Yara_rule()
        yara_rule.name = yara_dict["rule_name"]

        yara_metadata = {key.lower(): val.strip().strip("\"") for key, val in
                         yara_dict["metadata"].iteritems()} if "metadata" in yara_dict else {}
        for possible_field, mapped_to in metadata_field_mapping.iteritems():
            mapped_to = mapped_to.lower()
            possible_field = possible_field.lower()
            if possible_field in yara_metadata.keys():
                field = yara_metadata[possible_field] if not mapped_to in ["confidence", "eventid"] else int(
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

                if mapped_to in cls.__table__.columns.keys():
                    setattr(yara_rule, mapped_to, field)
                else:
                    if mapped_to in metadata_fields.keys():
                        to_field = metadata_fields[mapped_to]
                        fields_to_add.append(MetadataMapping(value=field, metadata_id=to_field.id))

        # yara_rule.condition = " ".join(yara_dict["condition_terms"])
        # yara_rule.strings = "\n".join(
        #    ["%s = %s %s" % (r["name"], r["value"], " ".join(r["modifiers"]) if "modifiers" in r else "") for r in
        #     yara_dict["strings"]])
        yara_rule.condition = "\n" + condition
        yara_rule.strings = "\n" + strings if strings else ""
        yara_rule.imports = imports

        if not yara_rule.category:
            yara_rule.category = CfgCategoryRangeMapping.DEFAULT_CATEGORY
        return yara_rule, fields_to_add


@listens_for(Yara_rule, "before_insert")
def generate_eventid(mapper, connect, target):
    if not current_user.admin:
        release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
        if release_state and target.state == release_state.state:
            abort(403)

    target.name = re.sub("[^A-Za-z0-9_]", "", target.name)

    if not target.eventid:
        target.eventid = CfgCategoryRangeMapping.get_next_category_eventid(target.category)


@listens_for(Yara_rule, "before_update")
def yara_rule_before_update(mapper, connect, target):
    target.name = re.sub("[^A-Za-z0-9_]", "", target.name)

    if not current_user.admin:
        release_state = cfg_states.Cfg_states.query.filter(cfg_states.Cfg_states.is_release_state > 0).first()
        if release_state and target.state == release_state.state:
            abort(403)


class Yara_rule_history(db.Model):
    __tablename__ = "yara_rules_history"

    id = db.Column(db.Integer, primary_key=True)

    date_created = db.Column(db.DateTime(timezone=True))
    revision = db.Column(db.Integer(unsigned=True))
    state = db.Column(db.String(32), index=True)

    _rule_json = db.Column(db.LargeBinary, nullable=False)

    yara_rule_id = db.Column(db.Integer, db.ForeignKey("yara_rules.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    user = db.relationship('KBUser', foreign_keys=user_id,
                           primaryjoin="KBUser.id==Yara_rule_history.user_id")

    @property
    def rule_json(self):
        try:
            return zlib.decompress(self._rule_json)
        except:
            return self._rule_json

    @rule_json.setter
    def rule_json(self, value):
        self._rule_json = zlib.compress(value, 8)

    @property
    def release_data_dict(self):
        return json.loads(self.release_data) if self.release_data else {}

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            revision=self.revision,
            rule_json=json.loads(self.rule_json),
            yara_rule_id=self.yara_rule_id,
            user=self.user.to_dict(),
            state=self.state
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
