"""default tags

Revision ID: 0e2074fb38e8
Revises: b8ab35edf211
Create Date: 2017-10-30 23:20:11.290244

"""
from alembic import op
import sqlalchemy as sa
from app.models import tags

# revision identifiers, used by Alembic.
revision = '0e2074fb38e8'
down_revision = 'b8ab35edf211'
branch_labels = None
depends_on = None


def upgrade():
    op.bulk_insert(
        tags.Tags.__table__, [
            {"text": "Suspicous Javascript"},
            {"text": "Malware"}
        ]
    )


def downgrade():
    op.execute("""DELETE from tags;""")
