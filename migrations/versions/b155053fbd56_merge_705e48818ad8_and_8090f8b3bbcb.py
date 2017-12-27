"""merge 705e48818ad8 and 8090f8b3bbcb

Revision ID: b155053fbd56
Revises: 8090f8b3bbcb, 705e48818ad8
Create Date: 2017-12-01 22:03:13.334684

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b155053fbd56'
down_revision = ('8090f8b3bbcb', '705e48818ad8')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
