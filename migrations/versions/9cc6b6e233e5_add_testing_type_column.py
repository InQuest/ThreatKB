"""Add testing type column

Revision ID: 9cc6b6e233e5
Revises: 695612f2c4ad
Create Date: 2019-02-21 14:42:46.631917

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9cc6b6e233e5'
down_revision = '695612f2c4ad'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('yara_testing_history', sa.Column('test_type', sa.String(32), nullable=False))


def downgrade():
    op.drop_column('yara_testing_history', 'test_type')
