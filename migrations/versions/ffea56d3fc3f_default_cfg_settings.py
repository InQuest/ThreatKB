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
             "date_modified": date_modified, "description": "Relative path to the nav image in the header."},
            {"key": "REDIS_BROKER_URL", "value": "redis://localhost:6379/0", "public": True,
             "date_created": date_created, "date_modified": date_modified,
             "description": "Redis broker url. Used for asynchronous testing with Celery."},
            {"key": "REDIS_TASK_SERIALIZER", "value": "json", "public": True, "date_created": date_created,
             "date_modified": date_modified, "description": "Task serializer to use with redis and Celery."},
            {"key": "REDIS_RESULT_SERIALIZER", "value": "json", "public": True, "date_created": date_created,
             "date_modified": date_modified, "description": "Task result serializer to use with redis and Celery."},
            {"key": "REDIS_ACCEPT_CONTENT", "value": "[\"json\"]", "public": True, "date_created": date_created,
             "date_modified": date_modified, "description": "Redis accept content format."},
            {"key": "MAX_MILLIS_PER_FILE_THRESHOLD", "value": "3.0", "public": True, "date_created": date_created,
             "date_modified": date_modified, "description": "Max milliseconds before timeout when testing files."},
            {"key": "FILE_STORE_PATH", "value": "/usr/local/ThreatKB/", "public": True, "date_created": date_created,
             "date_modified": date_modified, "description": "File storage location for attachments to signatures."},
            {"key": "DEFAULT_METADATA_MAPPING",
             "value": "{\"description\": \"description\",\"confidence\": \"confidence\",\"test_status\": \"test_status\",\"severity\": \"severity\",\"category\": \"category\",\"file_type\": \"file_type\",\"subcategory1\": \"subcategory1\",\"subcategory2\": \"subcategory2\",\"subcategory3\": \"subcategory3\",\"reference_link\": \"reference_link\",\"eventid\": \"eventid\",\"revision\": \"revision\",\"last_revision_date\": \"last_revision_date\"}",
             "public": True, "date_created": date_created, "date_modified": date_modified,
             "description": "The mapping to use for importing metadata in key/value format. The key is the source metadata field and the destination is the ThreatKB metadata field. The ThreatKB metadata field must exist in the system!"}
        ]
    )


def downgrade():
    keys = ["NAV_IMAGE", "REDIS_BROKER_URL", "REDIS_TASK_SERIALIZER", "REDIS_RESULT_SERIALIZER",
            "REDIS_ACCEPT_CONTENT", "MAX_MILLIS_PER_FILE_THRESHOLD"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))
