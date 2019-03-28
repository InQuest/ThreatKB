"""add indexes

Revision ID: 650b0ad88d25
Revises: d8a036ecf92d
Create Date: 2019-03-27 20:34:41.626587

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '650b0ad88d25'
down_revision = 'd8a036ecf92d'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE INDEX ifx_yara_rules_description ON yara_rules (`description`(1000));""")
    op.execute("""CREATE INDEX ifx_yara_rules_references ON yara_rules (`references`(1000));""")
    op.execute("""CREATE INDEX ifx_yara_rules_condition ON yara_rules (`condition`(1000));""")
    op.execute("""CREATE INDEX ifx_yara_rules_strings ON yara_rules (`strings`(1000));""")


def downgrade():
    op.execute("""DROP INDEX ifx_yara_rules_description ON yara_rules;""")
    op.execute("""DROP INDEX ifx_yara_rules_references ON yara_rules;""")
    op.execute("""DROP INDEX ifx_yara_rules_condition ON yara_rules;""")
    op.execute("""DROP INDEX ifx_yara_rules_strings ON yara_rules;""")
