"""
Celery configuration for agent project.
"""
import os
from celery import Celery
from celery.schedules import crontab
from monitoring import constants

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

app = Celery('agent')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'ping-devices': {
        'task': 'monitoring.tasks.ping_all_devices',
        'schedule': constants.PING_INTERVAL_SECONDS,
    },
    'send-heartbeat': {
        'task': 'monitoring.tasks.send_heartbeat_to_cloud',
        'schedule': 300.0,  # Every 5 minutes
    },
    'send-hourly-summary': {
        'task': 'monitoring.tasks.send_hourly_summary_to_cloud',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
    'update-system-heartbeat': {
        'task': 'monitoring.tasks.update_system_heartbeat',
        'schedule': 30.0,  # Every 30 seconds
    },
    'retry-unsynced-summaries': {
        'task': 'monitoring.tasks.retry_unsynced_summaries',
                'schedule': 900.0,  # 900s = 15 minutes
    },
}

# Simplify log format - remove worker names and log levels
app.conf.worker_log_format = '%(asctime)s: %(message)s'
app.conf.worker_task_log_format = '%(asctime)s: %(message)s'
