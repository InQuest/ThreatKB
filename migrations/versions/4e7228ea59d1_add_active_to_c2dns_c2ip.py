"""add active to c2dns/c2ip

Revision ID: 4e7228ea59d1
Revises: fe5820317f46
Create Date: 2019-04-06 12:28:04.881531

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4e7228ea59d1'
down_revision = 'fe5820317f46'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('c2dns', sa.Column('active', sa.Boolean(), nullable=False))
    op.create_index('ix_c2dns_active', 'c2dns', ['active'], unique=False)
    op.execute("""UPDATE c2dns set active=1;""")
    op.add_column('c2ip', sa.Column('active', sa.Boolean(), nullable=False))
    op.create_index('ix_c2ip_active', 'c2ip', ['active'], unique=False)
    op.execute("""UPDATE c2ip set active=1;""")
    op.create_index('ix_yara_rules_active', 'yara_rules', ['active'], unique=False)


def downgrade():
    op.drop_index('ix_yara_rules_active', table_name='yara_rules')
    op.drop_index('ix_c2ip_active', table_name='c2ip')
    op.drop_column('c2ip', 'active')
    op.drop_index('ix_c2dns_active', table_name='c2dns')
    op.drop_column('c2dns', 'active')
