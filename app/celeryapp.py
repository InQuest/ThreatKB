from celery import Celery

from app import app
from app.models import cfg_settings

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
