"""Add uniqueness config for c2ip/dns

Revision ID: dee9fac06614
Revises: 4e7228ea59d1
Create Date: 2019-04-06 12:34:10.259619

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import datetime
from app.models.cfg_settings import Cfg_settings

# revision identifiers, used by Alembic.
revision = 'dee9fac06614'
down_revision = '4e7228ea59d1'
branch_labels = None
depends_on = None


def upgrade():
    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        Cfg_settings.__table__,
        [
            {"key": "ENFORCE_UNIQUE_C2IP", "value": "0", "public": True, "date_created": date_created,
             "date_modified": date_modified,
             "description": "If true, don't allow duplicate c2 ip address."},
            {"key": "ENFORCE_UNIQUE_C2DNS", "value": "0", "public": True, "date_created": date_created,
             "date_modified": date_modified,
             "description": "If true, don't allow duplicate c2 dns domains."},
        ]
    )


def downgrade():
    keys = ["ENFORCE_UNIQUE_C2IP", "ENFORCE_UNIQUE_C2DNS"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))
