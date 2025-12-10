# fastapi_app/main.py
import os
import django
import logging
from fastapi import FastAPI

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")
django.setup()

from .api.routes.bot_api import router as bot_router
from .api.routes.webhooks.notify import router as notify_router
from .api.routes.webhooks.user import router as user_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# TO‘G‘RI PREFIX — Run Bot ishlaydi!
app.include_router(bot_router, prefix="/api/bots")           # /api/bots/run/5
app.include_router(notify_router, prefix="/api/webhooks")    # /api/webhooks/handle-user-completed
app.include_router(user_router, prefix="/api/webhooks/user") # /api/webhooks/user/5

@app.get("/")
async def root():
    return {"status": "OK", "message": "FastAPI ishlayapti!"}