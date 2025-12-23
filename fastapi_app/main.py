# fastapi_app/main.py
"""
FastAPI application main file
"""
import os
import sys
import logging
from pathlib import Path

# Django settings
sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')

import django
django.setup()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from fastapi_app.api.routes.webhooks.main_bot import router as main_bot_router
from fastapi_app.api.routes.webhooks.notify import router as notification_router
from fastapi_app.api.routes.bot_api import router as bot_api_router
from fastapi_app.api.routes.webhooks.dispatch import router as dispatch_router  # Sizning oddiy dispatch
from fastapi_app.workers.batch_processor import BatchProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Telegram Bot API",
    description="Main bot webhook and admin panel API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with CORRECT prefixes
app.include_router(
    main_bot_router,
    prefix="/webhook",  # Telegram /webhook uchun
    tags=["Webhooks"]
)

app.include_router(
    notification_router,
    prefix="/api/webhooks",  # Ichki API uchun (handle-user-completed)
    tags=["Internal Webhooks"]
)

app.include_router(
    bot_api_router,
    prefix="/api/bots",  # Bot management API
    tags=["Bot Management"]
)

# Dispatch router (sizning oddiy versiya)
app.include_router(
    dispatch_router,
    prefix="/api/webhooks/dispatch",
    tags=["B Bot Webhooks"]
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("🚀 Starting FastAPI application...")

    # Start batch processor
    try:
        batch_processor = BatchProcessor()
        await batch_processor.start()
        logger.info("✅ Batch processor started")
    except Exception as e:
        logger.error(f"❌ Failed to start batch processor: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("👋 Shutting down FastAPI application...")

# Health check
@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "Telegram Bot API",
        "version": "1.0.0"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}