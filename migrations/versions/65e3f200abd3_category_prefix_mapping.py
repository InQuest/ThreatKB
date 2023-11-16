"""Category Prefix Mapping

Revision ID: 65e3f200abd3
Revises: fc0cab9d77dc
Create Date: 2023-05-31 21:05:32.214274

"""
import datetime

from alembic import op
from app.models import cfg_settings

# revision identifiers, used by Alembic.
revision = '65e3f200abd3'
down_revision = 'fc0cab9d77dc'
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
                "key": "CATEGORY_PREFIX_MAPPING",
                "value": "{ \"Hunt Pivots\": \"HP\", \"Evasion Characteristics\": \"EC\", \"File Characteristics\": \"FC\", \"FileID\": \"FID\", \"Suspicious Characteristics\": \"SC\", \"Malicious Characteristics\": \"MC\", \"Header Analytics\": \"HA\", \"Light House\" : \"LH\", \"Data Loss\": \"DL\", \"Template\": \"UD\", \"Retention\": \"RET\" }",
                "public": True,
                "date_created": date_created,
                "date_modified": date_modified,
                "description": "The mapping between categories and their rule prefixes."
            }
        ]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    keys = ["CATEGORY_PREFIX_MAPPING"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))

    # ### end Alembic commands ###