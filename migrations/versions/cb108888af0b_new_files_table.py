"""new files table

Revision ID: cb108888af0b
Revises: b315f76a9a56
Create Date: 2017-08-08 21:00:57.766548

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb108888af0b'
down_revision = 'b315f76a9a56'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date_created', sa.DateTime(timezone=True), nullable=True),
    sa.Column('date_modified', sa.DateTime(timezone=True), nullable=True),
    sa.Column('filename', sa.String(length=65000), nullable=True),
    sa.Column('content_type', sa.String(length=100), nullable=True),
    sa.Column('entity_type', sa.Integer(), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['kb_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(u'ix_files_entity_id', 'files', ['entity_id'], unique=False)
    op.create_index(u'ix_files_entity_type', 'files', ['entity_type'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(u'ix_files_entity_type', table_name='files')
    op.drop_index(u'ix_files_entity_id', table_name='files')
    op.drop_table('files')
    # ### end Alembic commands ###
