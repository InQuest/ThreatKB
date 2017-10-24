"""default cfg_settings

Revision ID: ffea56d3fc3f
Revises: 38aa862c0a93
Create Date: 2017-09-17 11:16:07.252228

"""
from alembic import op
from app.models import cfg_settings
import sqlalchemy as sa
import datetime

# revision identifiers, used by Alembic.
revision = 'ffea56d3fc3f'
down_revision = '38aa862c0a93'
branch_labels = None
depends_on = None


def upgrade():
    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        cfg_settings.Cfg_settings.__table__,
        [
            {"key": "NAV_IMAGE", "value": "inquest_logo.svg", "public": True, "date_created": date_created,
             "date_modified": date_modified},
            {"key": "YARA_PATH", "value": "/usr/local/bin/yara", "public": True, "date_created": date_created,
             "date_modified": date_modified},
            {"key": "CLEAN_FILES_CORPUS_DIRECTORY", "value": "files/clean/", "public": True,
             "date_created": date_created, "date_modified": date_modified},
            {"key": "ATTACHED_FILES_CORPUS_DIRECTORY", "value": "files/attached/", "public": True,
             "date_created": date_created, "date_modified": date_modified},
            {"key": "ATTACHED_FILES_PREPROCESSOR", "value": "", "public": True, "date_created": date_created,
             "date_modified": date_modified},
            {"key": "REDIS_BROKER_URL", "value": "redis://localhost:6379/0", "public": False,
             "date_created": date_created, "date_modified": date_modified},
            {"key": "REDIS_TASK_SERIALIZER", "value": "json", "public": False, "date_created": date_created,
             "date_modified": date_modified},
            {"key": "REDIS_RESULT_SERIALIZER", "value": "json", "public": False, "date_created": date_created,
             "date_modified": date_modified},
            {"key": "REDIS_ACCEPT_CONTENT", "value": "[\"json\"]", "public": False, "date_created": date_created,
             "date_modified": date_modified},
            {"key": "MAX_MILLIS_PER_FILE_THRESHOLD", "value": "3.0", "public": False, "date_created": date_created,
             "date_modified": date_modified},
            {"key": "FILE_STORE_PATH", "value": "/usr/local/ThreatKB/", "public": True, "date_created": date_created,
             "date_modified": date_modified},
            {"key": "DEFAULT_METADATA_MAPPING",
             "value": "{\"description\": \"description\",\"confidence\": \"confidence\",\"test_status\": \"test_status\",\"severity\": \"severity\",\"category\": \"category\",\"file_type\": \"file_type\",\"subcategory1\": \"subcategory1\",\"subcategory2\": \"subcategory2\",\"subcategory3\": \"subcategory3\",\"reference_link\": \"reference_link\",\"eventid\": \"eventid\",\"revision\": \"revision\",\"last_revision_date\": \"last_revision_date\"}",
             "public": True, "date_created": date_created, "date_modified": date_modified}
        ]
    )


def downgrade():
    keys = ["NAV_IMAGE", "YARA_PATH", "CLEAN_FILES_CORPUS_DIRECTORY", "ATTACHED_FILES_CORPUS_DIRECTORY",
            "ATTACHED_FILES_PREPROCESSOR", "REDIS_BROKER_URL", "REDIS_TASK_SERIALIZER", "REDIS_RESULT_SERIALIZER",
            "REDIS_ACCEPT_CONTENT", "MAX_MILLIS_PER_FILE_THRESHOLD"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))
