from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app import app, db


app.config.from_object('config')

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    """Below imports needed for migration"""
    from app.models import users
    from app.models import c2ip
    from app.models import c2dns
    from app.models import cfg_settings
    from app.models import yara_rule
    from app.models import cfg_states
    from app.models import comments
    from app.models import tags
    from app.models import tags_mapping
    from app.models import files
    from app.models import cfg_category_range_mapping
    from app.models import releases
    from app.models import tasks
    from app.models import access_keys
    from app.models import whitelist

    manager.run()
