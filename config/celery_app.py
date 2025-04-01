# Django settings
import os
from django.conf import settings
# Celery app
from celery import Celery
import logging


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config', broker='redis://localhost')

# namespace='CELERY' means all celery-related configuration keys
# should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure logging
logger = logging.getLogger('celery')
logger.setLevel(logging.DEBUG) # or DEBUG, WARNING, ERROR, etc.

# Example file handler:
file_handler = logging.FileHandler('/home/alex/Downloads/celery.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
