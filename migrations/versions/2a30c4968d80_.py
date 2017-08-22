"""Merge revision branches

Revision ID: 2a30c4968d80
Revises: 3a3368610e08, b90dcb36a10a
Create Date: 2017-08-22 15:29:04.446725

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2a30c4968d80'
down_revision = ('3a3368610e08', 'b90dcb36a10a')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
