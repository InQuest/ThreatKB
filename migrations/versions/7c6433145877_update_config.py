"""Update config

Revision ID: 7c6433145877
Revises: b5357371ee6d
Create Date: 2017-08-18 12:22:54.682578

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7c6433145877'
down_revision = 'b5357371ee6d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('config', 'id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('config', sa.Column('id', mysql.INTEGER(display_width=11), nullable=False))
    # ### end Alembic commands ###
