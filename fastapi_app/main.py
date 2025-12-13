import os
import django
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")
django.setup()

load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle"""
    # Startup
    from shared.redis_client import redis_client

    if redis_client.is_connected():
        logger.info("✅ Redis connected successfully")
    else:
        logger.warning("⚠️ Redis not connected")

    # Import and start workers
    from fastapi_app.workers.batch_processor import BatchProcessor
    from fastapi_app.workers.bot_worker import BotWorkerPool

    batch_processor = BatchProcessor()
    await batch_processor.start()

    logger.info("✅ Application started successfully")

    yield

    # Shutdown
    await batch_processor.stop()
    logger.info("🛑 Application shutting down")


# Create FastAPI app
app = FastAPI(
    title="Konkurs Bot System",
    description="High-performance Telegram bot competition platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Productionda aniq domainlar berish kerak
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from fastapi_app.api.routes.bot_api import router as bot_router
from fastapi_app.api.routes.webhooks.main_bot import router as webhook_main_router
from fastapi_app.api.routes.webhooks.dispatch import router as webhook_dispatch_router

# Include routers with correct prefixes
app.include_router(bot_router, prefix="/api/bots", tags=["Bots Management"])
app.include_router(webhook_main_router, prefix="/api/webhooks", tags=["Main Bot Webhooks"])
app.include_router(webhook_dispatch_router, prefix="/api/webhooks", tags=["B Bots Webhooks"])


# Root endpoint
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Konkurs Bot System",
        "version": "2.0.0",
        "endpoints": {
            "bot_management": "/api/bots",
            "main_webhooks": "/api/webhooks/handle-user-completed",
            "b_bot_webhooks": "/api/webhooks/dispatch/{bot_id}",
            "docs": "/docs",
            "health": "/health"
        }
    }


# Health check endpoint
@app.get("/health")
async def health():
    """Health check for monitoring"""
    from shared.redis_client import redis_client
    from django.db import connection

    health_status = {
        "status": "healthy",
        "timestamp": django.utils.timezone.now().isoformat(),
        "components": {
            "api": "healthy",
            "redis": "healthy" if redis_client.is_connected() else "unhealthy",
            "database": "unhealthy"
        }
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["components"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    # Agar bitta component ham unhealthy bo'lsa
    if any(status == "unhealthy" for status in health_status["components"].values()):
        health_status["status"] = "degraded"

    return health_status


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)[:200]
        }
    )


# 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Endpoint not found: {request.url.path}"}
    )