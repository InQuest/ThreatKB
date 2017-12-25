from app import db
from dateutil import parser


class Metadata(db.Model):
    __tablename__ = "metadata"

    TYPES = ["string", "integer", "date", "multiline_comment"]

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), nullable=False)

    active = db.Column(db.Boolean, nullable=False, default=True)

    artifact_type = db.Column(db.Integer, nullable=False)
    type_ = db.Column(db.String(128), nullable=False)
    default = db.Column(db.String(4096), nullable=True)

    show_in_table = db.Column(db.Integer, default=0, nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==Metadata.created_user_id")
    choices = db.relationship('MetadataChoices', primaryjoin="MetadataChoices.metadata_id==Metadata.id")

    def to_dict(self, include_mappings=False):
        try:
            default = int(self.default)
        except:
            try:
                default = parser.parse(self.default).isoformat()
            except:
                default = self.default

        results = dict(
            id=self.id,
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            created_user=self.created_user.to_dict(),
            key=self.key,
            artifact_type=self.artifact_type,
            type=self.type_,
            default=default,
            show_in_table=self.show_in_table,
            active=self.active,
            choices=[choice.to_dict() for choice in self.choices]
        )

        if include_mappings and self.active:
            results["mappings"] = [entity.to_dict() for entity in db.session.query(MetadataMapping).filter(
                MetadataMapping.metadata_id == self.id).all()]

        return results

    def __repr__(self):
        return '<Metadata %r>' % self.id


class MetadataMapping(db.Model):
    __tablename__ = "metadata_mapping"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(60000), nullable=True)

    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    metadata_id = db.Column(db.Integer, db.ForeignKey('metadata.id'), nullable=False)
    metadata_object = db.relationship('Metadata', foreign_keys=metadata_id,
                                      primaryjoin="Metadata.id==MetadataMapping.metadata_id")
    artifact_id = db.Column(db.Integer, nullable=False)
    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==MetadataMapping.created_user_id")

    def to_dict(self):
        return dict(
            id=self.id,
            value=self.value,
            metadata=self.metadata_object.to_dict(),
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            created_user=self.created_user.to_dict()
        )

    def __repr__(self):
        return '<MetadataMapping %r>' % self.id


class MetadataChoices(db.Model):
    __tablename__ = "metadata_choices"

    id = db.Column(db.Integer, primary_key=True)
    choice = db.Column(db.String(512), nullable=False)

    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    metadata_id = db.Column(db.Integer, db.ForeignKey('metadata.id'), nullable=False)
    metadata_object = db.relationship('Metadata', foreign_keys=metadata_id,
                                      primaryjoin="Metadata.id==MetadataChoices.metadata_id")
    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==MetadataChoices.created_user_id")

    def to_dict(self):
        return dict(
            id=self.id,
            choice=self.choice,
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            created_user=self.created_user.to_dict()
        )

    def __repr__(self):
        return '<MetadataChoices %r>' % self.id
