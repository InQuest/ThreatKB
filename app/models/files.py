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
    filename = db.Column(db.String(65000))
    directory = db.Column(db.String(2048))
    content_type = db.Column(db.String(100))
    entity_type = db.Column(db.Integer(), index=True, nullable=True)
    entity_id = db.Column(db.Integer(), index=True, nullable=True)
    sha256 = db.Column(db.String(64), nullable=True)
    md5 = db.Column(db.String(32), nullable=True)
    sha1 = db.Column(db.String(40), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    user = db.relationship('KBUser', foreign_keys=user_id)

    def to_dict(self):
        return dict(
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            filename=self.filename,
            directory=self.directory,
            content_type=self.content_type,
            entity_type=list(ENTITY_MAPPING.keys())[list(ENTITY_MAPPING.values()).index(self.entity_type)]
            if self.entity_type else None,
            entity_id=self.entity_id if self.entity_id else None,
            id=self.id,
            user=self.user.to_dict(),
            sha1=self.sha1,
            md5=self.md5,
            sha256=self.sha256
        )

    def get_file_path(self):
        file_store_path = Cfg_settings.get_setting("FILE_STORE_PATH")
        return os.path.join(file_store_path,
                            str(self.entity_type) if self.entity_type is not None else "",
                            str(self.entity_id) if self.entity_id is not None else "",
                            str(self.directory) if self.directory is not None else "",
                            str(self.filename))

    def get_relative_file_path(self):
        return os.path.join(str(self.entity_id) if self.entity_id is not None else "",
                            str(self.directory) if self.directory is not None else "",
                            str(self.filename))

    @staticmethod
    def get_path_for_file(entity_type, entity_id, directory=None, filename=None):
        file_store_path = Cfg_settings.get_setting("FILE_STORE_PATH")
        return os.path.join(file_store_path,
                     str(entity_type) if entity_type is not None else "",
                     str(entity_id) if entity_id is not None else "",
                     str(directory) if directory is not None else "",
                     str(filename) if filename is not None else "")


    def __repr__(self):
        return '<Files %r>' % self.id
