from celery import Celery

from app import app
from app.models import cfg_settings


app.config["BROKER_URL"] = cfg_settings.Cfg_settings.get_private_setting("REDIS_BROKER_URL")
app.config["TASK_SERIALIZER"] = cfg_settings.Cfg_settings.get_private_setting("REDIS_TASK_SERIALIZER")
app.config["RESULT_SERIALIZER"] = cfg_settings.Cfg_settings.get_private_setting("REDIS_RESULT_SERIALIZER")
app.config["ACCEPT_CONTENT"] = cfg_settings.Cfg_settings.get_private_setting("REDIS_ACCEPT_CONTENT")
app.config["FILE_STORE_PATH"] = cfg_settings.Cfg_settings.get_private_setting("FILE_STORE_PATH")
app.config["MAX_MILLIS_PER_FILE_THRESHOLD"] = cfg_settings.Cfg_settings.get_private_setting(
    "MAX_MILLIS_PER_FILE_THRESHOLD")

if app.config["MAX_MILLIS_PER_FILE_THRESHOLD"]:
    app.config["MAX_MILLIS_PER_FILE_THRESHOLD"] = float(app.config["MAX_MILLIS_PER_FILE_THRESHOLD"])


def make_celery(flask_app):
    celery_app = Celery(flask_app.import_name,
                        backend=flask_app.config['BROKER_URL'],
                        broker=flask_app.config['BROKER_URL'])
    celery_app.conf.update(flask_app.config)
    # task_base = celery_app.Task
    #
    # class ContextTask(task_base):
    #     abstract = True
    #
    #     def __call__(self, *args, **kwargs):
    #         with flask_app.app_context():
    #             return task_base.__call__(self, *args, **kwargs)
    #
    # celery_app.Task = ContextTask

    return celery_app


celery = make_celery(app)
