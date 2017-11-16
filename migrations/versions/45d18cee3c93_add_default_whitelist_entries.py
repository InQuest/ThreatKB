"""Add default whitelist entries

Revision ID: 45d18cee3c93
Revises: 76ac9b0bf6e7
Create Date: 2017-10-30 15:19:57.648437

"""
from alembic import op
import sqlalchemy as sa
from app.models import whitelist
import datetime

# revision identifiers, used by Alembic.
revision = '45d18cee3c93'
down_revision = '76ac9b0bf6e7'
branch_labels = None
depends_on = None


def upgrade():
    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        whitelist.Whitelist.__table__, [
            {"whitelist_artifact": "127.0.0.0/8", "notes": "Loopback range", "created_time": date_created,
             "modified_time": date_modified},
            {"whitelist_artifact": "localhost", "notes": "Loopback range", "created_time": date_created,
             "modified_time": date_modified},
            {"whitelist_artifact": "8.8.8.8/32", "notes": "Google DNS", "created_time": date_created,
             "modified_time": date_modified},
            {"whitelist_artifact": "8.8.4.4/32", "notes": "Google DNS", "created_time": date_created,
             "modified_time": date_modified},
            {"whitelist_artifact": "10.0.0.0/8", "notes": "RFC1918 Private Range", "created_time": date_created,
             "modified_time": date_modified},
            {"whitelist_artifact": "192.168.0.0/16", "notes": "RFC1918 Private Range", "created_time": date_created,
             "modified_time": date_modified},
            {"whitelist_artifact": "172.16.0.0/12", "notes": "RFC1918 Private Range", "created_time": date_created,
             "modified_time": date_modified},
            {"whitelist_artifact": "(^|[\.\/])google\.com", "notes": "Google DNS", "created_time": date_created,
             "modified_time": date_modified},
            {"whitelist_artifact": "(^|[\.\/])microsoft\.com", "notes": "Microsoft DNS", "created_time": date_created,
             "modified_time": date_modified},
        ]
    )


def downgrade():
    op.execute("""DELETE from whitelist;""")
