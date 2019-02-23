"""remove nullable and add total_files

Revision ID: d8a036ecf92d
Revises: 63a47ddd8717
Create Date: 2019-02-23 13:22:41.722782

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'd8a036ecf92d'
down_revision = '63a47ddd8717'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('yara_testing_history', sa.Column('total_files', sa.Integer(), nullable=False))
    op.add_column('yara_testing_history', sa.Column('status', sa.String(32), nullable=False))
    op.alter_column('yara_testing_history', 'end_time',
                    existing_type=sa.DATETIME(),
                    type_=sa.DateTime(timezone=True),
                    nullable=True)
    op.alter_column('yara_testing_history', 'files_matched',
                    existing_type=mysql.INTEGER(display_width=11),
                    nullable=True)
    op.alter_column('yara_testing_history', 'files_tested',
                    existing_type=mysql.INTEGER(display_width=11),
                    nullable=True)


def downgrade():
    op.alter_column('yara_testing_history', 'files_tested',
                    existing_type=mysql.INTEGER(display_width=11),
                    nullable=False)
    op.alter_column('yara_testing_history', 'files_matched',
                    existing_type=mysql.INTEGER(display_width=11),
                    nullable=False)
    op.alter_column('yara_testing_history', 'end_time',
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.DATETIME(),
                    nullable=False)
    op.drop_column('yara_testing_history', 'total_files')
    op.drop_column('yara_testing_history', 'status')
