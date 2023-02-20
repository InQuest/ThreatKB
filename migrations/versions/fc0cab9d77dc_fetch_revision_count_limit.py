"""Fetch Revision Count Limit

Revision ID: fc0cab9d77dc
Revises: a688cf44cd8a
Create Date: 2023-02-19 22:45:12.789465

"""
import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
from app.models import cfg_settings

revision = 'fc0cab9d77dc'
down_revision = 'a688cf44cd8a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        cfg_settings.Cfg_settings.__table__,
        [
            {
                "key": "FETCH_REVISION_COUNT_LIMIT",
                "value": "25",
                "public": True,
                "date_created": date_created,
                "date_modified": date_modified,
                "description": "The number of revisions to limit on fetch of Yara Rules."
            }
        ]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    keys = ["FETCH_REVISION_COUNT_LIMIT"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))

    # ### end Alembic commands ###
