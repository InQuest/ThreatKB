from app import db, ENTITY_MAPPING
from app.models.cfg_settings import Cfg_settings
import os


class Files(db.Model):
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True),
                             default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True),
                              default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    filename = db.Column(db.TEXT())
    content_type = db.Column(db.String(100))
    entity_type = db.Column(db.Integer(), index=True, nullable=True)
    entity_id = db.Column(db.Integer(), index=True, nullable=True)
    sha256 = db.Column(db.String(64), nullable=True)
    md5 = db.Column(db.String(32), nullable=True)
    sha1 = db.Column(db.String(40), nullable=True)
    parent_sha256 = db.Column(db.String(64), nullable=True)
    parent_md5 = db.Column(db.String(32), nullable=True)
    parent_sha1 = db.Column(db.String(32), nullable=True)
    path = db.Column(db.TEXT(), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    user = db.relationship('KBUser', foreign_keys=user_id)

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            filename=self.filename,
            content_type=self.content_type,
            entity_type=list(ENTITY_MAPPING.keys())[list(ENTITY_MAPPING.values()).index(self.entity_type)]
            if self.entity_type else None,
            entity_id=self.entity_id if self.entity_id else None,
            id=self.id,
            user=self.user.to_dict(),
            sha1=self.sha1,
            md5=self.md5,
            sha256=self.sha256,
            parent_md5=self.parent_md5,
            parent_sha1=self.parent_sha1,
            parent_sha256=self.parent_sha256,
            path=self.path,
            full_path=self.full_path,
            is_parent_file=self.is_parent_file
        )

    @property
    def full_path(self):
        root = Cfg_settings.get_setting("FILE_STORE_PATH") or "/tmp"
        temp_path = f"{root}{os.path.sep}{self.entity_type}{os.path.sep}{self.entity_id}{os.path.sep}"
        if self.parent_sha1:
            return f"{temp_path}{self.parent_sha1}{os.path.sep}{self.path}"
        else:
            return temp_path if os.path.exists(
                f"{temp_path}{self.filename}") else f"{temp_path}{os.path.sep}{self.sha1}"

    @property
    def is_parent_file(self):
        return True if self.parent_sha1 == None else False

    def __repr__(self):
        return '<Files %r>' % self.id
