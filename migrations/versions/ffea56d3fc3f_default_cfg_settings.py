"""default cfg_settings

Revision ID: ffea56d3fc3f
Revises: 38aa862c0a93
Create Date: 2017-09-17 11:16:07.252228

"""
from alembic import op
from app.models import cfg_settings
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ffea56d3fc3f'
down_revision = '38aa862c0a93'
branch_labels = None
depends_on = None


def upgrade():
    op.bulk_insert(
        cfg_settings.Cfg_settings.__table__,
        [
            {"key": "NAV_IMAGE", "value": "inquest_logo.svg", "public": True},
            {"key": "YARA_PATH", "value": "/usr/local/bin/yara", "public": True},
            {"key": "CLEAN_FILES_CORPUS_DIRECTORY", "value": "files/clean/", "public": True},
            {"key": "ATTACHED_FILES_CORPUS_DIRECTORY", "value": "files/clean/", "public": True},
            {"key": "ATTACHED_FILES_PREPROCESSOR", "value": "redis://localhost:6379/0", "public": True},
            {"key": "REDIS_BROKER_URL", "value": "redis://localhost:6379/0", "public": False},
            {"key": "REDIS_TASK_SERIALIZER", "value": "json", "public": False},
            {"key": "REDIS_RESULT_SERIALIZER", "value": "json", "public": False},
            {"key": "REDIS_ACCEPT_CONTENT", "value": "[\"json\"]", "public": False},
            {"key": "MAX_MILLIS_PER_FILE_THRESHOLD", "value": "redis://localhost:6379/0", "public": False}
        ]
    )


def downgrade():
    keys = ["NAV_IMAGE", "YARA_PATH", "CLEAN_FILES_CORPUS_DIRECTORY", "ATTACHED_FILES_CORPUS_DIRECTORY",
            "ATTACHED_FILES_PREPROCESSOR", "REDIS_BROKER_URL", "REDIS_TASK_SERIALIZER", "REDIS_RESULT_SERIALIZER",
            "REDIS_ACCEPT_CONTENT", "MAX_MILLIS_PER_FILE_THRESHOLD"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))
