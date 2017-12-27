"""Default dashboard release count

Revision ID: 3d8891a2dde0
Revises: b155053fbd56
Create Date: 2017-12-01 22:05:34.057072

"""
from alembic import op
import sqlalchemy as sa
import datetime
from app.models import cfg_settings

# revision identifiers, used by Alembic.
revision = '3d8891a2dde0'
down_revision = 'b155053fbd56'
branch_labels = None
depends_on = None


def upgrade():
    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        cfg_settings.Cfg_settings.__table__,
        [
            {"key": "DASHBOARD_RELEASES_COUNT", "value": '3', "public": True,
             "date_created": date_created,
             "date_modified": date_modified}
        ])


def downgrade():
    keys = ["DASHBOARD_RELEASES_COUNT"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))
