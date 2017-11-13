"""GEOIP database config settings

Revision ID: 665baa4d3f57
Revises: 34d5b6b940a7
Create Date: 2017-11-12 16:20:53.697870

"""
import datetime
from alembic import op

# revision identifiers, used by Alembic.
from app.models import cfg_settings

revision = '665baa4d3f57'
down_revision = '34d5b6b940a7'
branch_labels = None
depends_on = None


def upgrade():
    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        cfg_settings.Cfg_settings.__table__,
        [
            {"key": "GEOIP_ASN_DATABASE_FILE",
             "value": '/usr/local/ThreatKB/MaxMind/GeoLite2-ASN.mmdb',
             "public": True,
             "date_created": date_created,
             "date_modified": date_modified},
            {"key": "GEOIP_CITY_DATABASE_FILE",
             "value": '/usr/local/ThreatKB/MaxMind/GeoLite2-City.mmdb',
             "public": True,
             "date_created": date_created,
             "date_modified": date_modified}
        ]
    )


def downgrade():
    keys = ["GEOIP_ASN_DATABASE_FILE", "GEOIP_CITY_DATABASE_FILE"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % key)
