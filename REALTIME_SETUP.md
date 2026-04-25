"""
Settings and Configuration for Real-time Data Integration

Add these to your Django settings.py file:
"""

# ============================================================

# CACHING CONFIGURATION (for real-time data)

# ============================================================

# Using Redis (Recommended)

CACHES = {
'default': {
'BACKEND': 'django_redis.cache.RedisCache',
'LOCATION': 'redis://127.0.0.1:6379/1',
'OPTIONS': {
'CLIENT_CLASS': 'django_redis.client.DefaultClient',
}
}
}

# OR using local memory cache (for development)

# CACHES = {

# 'default': {

# 'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',

# 'LOCATION': 'unique-snowflake',

# }

# }

# ============================================================

# LOGGING CONFIGURATION (for debugging)

# ============================================================

LOGGING = {
'version': 1,
'disable_existing_loggers': False,
'formatters': {
'verbose': {
'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
'style': '{',
},
},
'handlers': {
'file': {
'level': 'ERROR',
'class': 'logging.FileHandler',
'filename': 'nifty100/logs/realtime_api.log',
'formatter': 'verbose',
},
'console': {
'level': 'DEBUG',
'class': 'logging.StreamHandler',
},
},
'loggers': {
'api.realtime_service': {
'handlers': ['file', 'console'],
'level': 'DEBUG',
'propagate': True,
},
},
}

# ============================================================

# REQUIRED PACKAGES

# ============================================================

# Add these to requirements.txt:

"""
requests>=2.28.0
django-redis>=5.2.0
redis>=4.3.0
yfinance>=0.1.74
"""

# ============================================================

# DATABASE MIGRATIONS

# ============================================================

# Run these commands:

"""
python manage.py makemigrations
python manage.py migrate
"""

# ============================================================

# SCHEDULED TASK (using celery-beat)

# ============================================================

# For periodic real-time data fetching, add this to celery config:

"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
'fetch-realtime-data': {
'task': 'api.tasks.fetch_realtime_data_task',
'schedule': crontab(minute='\*/15'), # Every 15 minutes
},
}
"""

# Then create api/tasks.py with:

"""
from celery import shared_task
from django.core.management import call_command

@shared_task
def fetch_realtime_data_task():
call_command('fetch_realtime_data')
"""
