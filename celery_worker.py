# celery_worker.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")

app = Celery('konkurs')
app.conf.broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app.conf.result_backend = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app.autodiscover_tasks(['fastapi_app.workers'])

if __name__ == "__main__":
    app.start()