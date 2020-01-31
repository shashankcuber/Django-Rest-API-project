# from celery import Celery
# from . import settings
# import os
# # from . import celeryconfig
# # from .phase1_2 import phase_1
# # os.environ.setdefault('DJANGO_SETTINGS_MODULE','bootcamp.settings')
# app=Celery('bootcamp')
# # app.config_from_object(celeryconfig)
# # worker_concurrency="2"
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bootcamp.settings')

app = Celery('bootcamp',backend='amqp://guest:guest@localhost',broker='amqp://guest:guest@localhost')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
