import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")
django.setup()

import logging
from fastapi import FastAPI
from .api.routes.bot_api import router as bot_router
from .api.routes.webhooks.notify import router as notify_router  # File name to'g'ri bo'lsa
from .api.routes.webhooks.user import router as user_webhook_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(bot_router, prefix="/api/bots")
app.include_router(notify_router, prefix="/api/webhooks/handle-user-completed")  # Fix: Specific prefix for this route
app.include_router(user_webhook_router, prefix="/api/webhooks")

@app.get("/")
async def root():
    return {"message": "API ishlamoqda!"}