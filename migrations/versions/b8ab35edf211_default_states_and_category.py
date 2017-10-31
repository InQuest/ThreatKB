"""default states and category

Revision ID: b8ab35edf211
Revises: 45d18cee3c93
Create Date: 2017-10-30 23:02:06.329870

"""
from alembic import op
import sqlalchemy as sa
import datetime
from app.models import cfg_category_range_mapping, cfg_states

# revision identifiers, used by Alembic.
revision = 'b8ab35edf211'
down_revision = '45d18cee3c93'
branch_labels = None
depends_on = None


def upgrade():
    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        cfg_category_range_mapping.CfgCategoryRangeMapping.__table__, [
            {"category": "Default", "range_min": 1, "range_max": 1000, "current": 0},
        ]
    )
    op.bulk_insert(
        cfg_states.Cfg_states.__table__, [
            {"state": "Production", "is_release_state": 1}
        ]
    )


def downgrade():
    op.execute("""DELETE from cfg_category_range_mapping;""")
    op.execute("""DELETE from cfg_states;""")
