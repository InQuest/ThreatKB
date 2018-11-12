"""Add default COMPILE_YARA_RULE_ON_SAVE setting

Revision ID: af2de80654b6
Revises: 2f0f6d26a505
Create Date: 2018-11-11 19:26:53.631142

"""
from alembic import op
import sqlalchemy as sa
from app.models import cfg_settings
import datetime
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'af2de80654b6'
down_revision = '2f0f6d26a505'
branch_labels = None
depends_on = None


def upgrade():
    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        cfg_settings.Cfg_settings.__table__,
        [
            {"key": "COMPILE_YARA_RULE_ON_SAVE", "value": "1", "public": True, "date_created": date_created,
             "date_modified": date_modified,
             "description": "If true, don't save yara rule changes unless they compile."},
        ]
    )


def downgrade():
    keys = ["COMPILE_YARA_RULE_ON_SAVE"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))
