"""Add directory to files model

Revision ID: e251ad2f9409
Revises: 5ce325a1b52e
Create Date: 2020-04-05 12:13:45.039418

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e251ad2f9409'
down_revision = '5ce325a1b52e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('files', sa.Column('directory', sa.Text(length=2048), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('files', 'directory')
    # ### end Alembic commands ###
