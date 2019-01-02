"""Add unique rulenames check config item

Revision ID: 695612f2c4ad
Revises: 8c3bbaef0f9c
Create Date: 2019-01-01 18:29:39.454540

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import datetime
from app.models.cfg_settings import Cfg_settings

# revision identifiers, used by Alembic.
revision = '695612f2c4ad'
down_revision = '8c3bbaef0f9c'
branch_labels = None
depends_on = None


def upgrade():
    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        Cfg_settings.__table__,
        [
            {"key": "ENFORCE_UNIQUE_YARA_RULE_NAMES", "value": "0", "public": True, "date_created": date_created,
             "date_modified": date_modified,
             "description": "If true, don't allow duplicate yara rule names."},
        ]
    )


def downgrade():
    keys = ["ENFORCE_UNIQUE_YARA_RULE_NAMES"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))
