import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hatch_messaging.settings")

app = Celery("hatch_messaging")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()