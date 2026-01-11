# fastapi_app/main.py
"""
FastAPI application main file
Vazifasi: FastAPI serverni ishga tushirish
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
from fastapi_app.api.routes.webhooks.dispatch import router as dispatch_router
from fastapi_app.api.routes.worker_api import router as worker_api_router
from fastapi_app.workers.batch_processor import BatchProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Konkurs Bot API",
    description="Telegram Bot Konkurs API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(main_bot_router, prefix="/webhook", tags=["Main Bot Webhooks"])
app.include_router(notification_router, prefix="/api/webhooks", tags=["Internal Webhooks"])
app.include_router(bot_api_router, prefix="/api/bots", tags=["Bot Management"])
app.include_router(dispatch_router, prefix="/api/webhooks/dispatch", tags=["B Bot Webhooks"])
app.include_router(worker_api_router, prefix="/api/workers", tags=["Worker Management"])


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting FastAPI application...")

    try:
        # Redis connection check
        from shared.redis_client import redis_client
        if redis_client.is_connected():
            logger.info("✅ Redis connected")
        else:
            logger.warning("⚠️ Redis not connected - running in fallback mode")

        # Batch processor
        batch_processor = BatchProcessor()
        await batch_processor.start()
        logger.info("✅ Batch processor started")

    except Exception as e:
        logger.error(f"❌ Startup error: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Shutting down FastAPI application...")

    try:
        # Stop all workers
        from fastapi_app.workers.bot_worker import worker_pool
        for bot_id in list(worker_pool.workers.keys()):
            await worker_pool.stop_worker(bot_id)
        logger.info("✅ All workers stopped")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "status": "running",
        "service": "Konkurs Bot API",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    from shared.redis_client import redis_client

    return {
        "status": "healthy",
        "redis_connected": redis_client.is_connected()
    }


@app.get("/api/status", tags=["Health"])
async def api_status():
    """API status endpoint"""
    from shared.redis_client import redis_client
    from fastapi_app.workers.bot_worker import worker_pool

    workers_status = await worker_pool.get_all_status()

    return {
        "status": "running",
        "redis": redis_client.is_connected(),
        "active_workers": len(workers_status),
        "workers": workers_status
    }# fastapi_app/main.py
"""
FastAPI application main file
"""
import os
import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
import django
django.setup()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_app.api.routes.webhooks.main_bot import router as main_bot_router
from fastapi_app.api.routes.webhooks.notify import router as notification_router
from fastapi_app.api.routes.bot_api import router as bot_api_router  #
from fastapi_app.api.routes.webhooks.dispatch import router as dispatch_router
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

# Include routers - BU YERDA PREFIX TO‘G‘RI BO‘LSIN!
app.include_router(main_bot_router, prefix="/webhook", tags=["Webhooks"])
app.include_router(notification_router, prefix="/api/webhooks", tags=["Internal Webhooks"])
app.include_router(bot_api_router, prefix="/api/bots", tags=["Bot Management"])  # <-- Bu qator muhim!
app.include_router(dispatch_router, prefix="/api/webhooks/dispatch", tags=["B Bot Webhooks"])


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting FastAPI application...")
    try:
        batch_processor = BatchProcessor()
        await batch_processor.start()
        logger.info("✅ Batch processor started")
    except Exception as e:
        logger.error(f"❌ Failed to start batch processor: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Shutting down FastAPI application...")


# Health check
@app.get("/")
async def root():
    return {"status": "running", "service": "Telegram Bot API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}



# Cache management endpoints
@app.post("/api/cache/clear/{bot_id}", tags=["Cache"])
async def clear_bot_cache(bot_id: int):
    """Bot cache ni tozalash"""
    from shared.redis_client import redis_client

    if not redis_client.is_connected():
        return {"status": "error", "message": "Redis not connected"}

    success = await redis_client.clear_bot_cache(bot_id)
    return {"status": "success" if success else "error", "bot_id": bot_id}


@app.post("/api/cache/refresh/{bot_id}", tags=["Cache"])
async def refresh_bot_cache(bot_id: int):
    """Bot cache ni yangilash"""
    from bots.user_bots.base_template.services.competition_service import CompetitionService

    service = CompetitionService()
    await service.update_cache(bot_id)

    return {"status": "success", "bot_id": bot_id, "message": "Cache refreshed"}