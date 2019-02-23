"""Add yara_testing_history_files_matches

Revision ID: 63a47ddd8717
Revises: 9cc6b6e233e5
Create Date: 2019-02-22 17:23:25.597951

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '63a47ddd8717'
down_revision = '9cc6b6e233e5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('yara_testing_history_files_matches',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('run_time', sa.Float(), nullable=False),
                    sa.Column('path', sa.String(length=5000), nullable=False),
                    sa.Column('stdout', sa.String(length=2000), nullable=True),
                    sa.Column('stderr', sa.String(length=2000), nullable=True),
                    sa.Column('command', sa.String(length=2000), nullable=True),
                    sa.Column('command_match_test_regex', sa.String(length=2000), nullable=True),
                    sa.Column('history_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['history_id'], ['yara_testing_history.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('yara_testing_history_files_matches')
