"""More default settings

Revision ID: 34d5b6b940a7
Revises: 9ada96d00858
Create Date: 2017-11-08 20:40:29.105752

"""
from alembic import op
import sqlalchemy as sa
import datetime
from app.models import cfg_settings

# revision identifiers, used by Alembic.
revision = '34d5b6b940a7'
down_revision = '9ada96d00858'
branch_labels = None
depends_on = None


def upgrade():
    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        cfg_settings.Cfg_settings.__table__,
        [
            {"key": "IMPORT_IP_REGEX", "value": '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:\/\d{1,3})?)',
             "public": True,
             "date_created": date_created,
             "description": "Regex to parse IP addresses from import text.",
             "date_modified": date_modified},
            {"key": "IMPORT_DNS_REGEX",
             "value": ur"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""",
             "public": True,
             "description": "Regex to parse DNS hostnames from import text.",
             "date_created": date_created, "date_modified": date_modified},
            {"key": "IMPORT_SIG_SPLIT_REGEX",
             "value": "\n[\t\s]*\}[\s\t]*(rule[\t\s][^\r\n]+(?:\{|[\r\n][\r\n\s\t]*\{))",
             "public": True,
             "description": "Regex to split yara rules when multiple are included in import text.",
             "date_created": date_created, "date_modified": date_modified},
            {"key": "IMPORT_SIG_PARSE_REGEX",
             "value": """^[\t\s]*rule[\t\s][^\r\n]+(?:\{|[\r\n][\r\n\s\t]*\{).*?condition:.*?\r?\n?[\t\s]*\}[\s\t]*(?:$|\r?\n)""",
             "public": True,
             "description": "Regex to parse out yara rules from import text",
             "date_created": date_created, "date_modified": date_modified},
            {"key": "NEGATIVE_TESTING_FILE_DIRECTORY",
             "value": """files/clean/""",
             "description": "Directory with files that should never file for any signature. Tested when you hit \"Clean Text Signature Now\"",
             "public": True,
             "date_created": date_created, "date_modified": date_modified},
            {"key": "RELEASE_PREPEND_TEXT",
             "value": "",
             "public": True,
             "description": "Prepend this text to generated release notes",
             "date_created": date_created, "date_modified": date_modified},
            {"key": "RELEASE_APPEND_TEXT",
             "value": "",
             "public": True,
             "description": "Append this text to generated release notes",
             "date_created": date_created, "date_modified": date_modified},

        ]
    )


def downgrade():
    keys = ["IMPORT_IP_REGEX", "IMPORT_DNS_REGEX", "IMPORT_SIG_SPLIT_REGEX", "IMPORT_SIG_PARSE_REGEX",
            "NEGATIVE_TESTING_FILE_DIRECTORY", "RELEASE_PREPEND_TEXT", "RELEASE_APPEND_TEXT"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))
