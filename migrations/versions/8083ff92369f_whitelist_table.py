"""whitelist table

Revision ID: 8083ff92369f
Revises: 9aadb08451dc
Create Date: 2017-10-01 23:13:06.948419

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8083ff92369f'
down_revision = '9aadb08451dc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('whitelist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('whitelist_artifact', sa.String(length=2048), nullable=True),
    sa.Column('notes', sa.String(length=2048), nullable=True),
    sa.Column('created_by_user_id', sa.Integer(), nullable=False),
    sa.Column('modified_by_user_id', sa.Integer(), nullable=False),
    sa.Column('created_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('modified_time', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['kb_users.id'], ),
    sa.ForeignKeyConstraint(['modified_by_user_id'], ['kb_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('whitelist')
    # ### end Alembic commands ###