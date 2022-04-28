"""Add activity_text_short

Revision ID: 5ce325a1b52e
Revises: 02a0ced07cb9
Create Date: 2020-04-05 11:06:19.815850

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '5ce325a1b52e'
down_revision = '02a0ced07cb9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('activity_log', sa.Column('activity_text_short', sa.Text(length=1000), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('activity_log', 'activity_text_short')
    # ### end Alembic commands ###
