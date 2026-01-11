# fastapi_app/api/routes/worker_api.py
"""
Worker API endpoints - TO'G'RILANGAN
Vazifasi: Worker larni boshqarish
"""
from fastapi import APIRouter, HTTPException
import logging

from shared.redis_client import redis_client
from fastapi_app.workers.bot_worker import worker_pool

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/start/{bot_id}")
async def start_worker(bot_id: int, worker_count: int = 1):
    """
    Bot uchun worker ishga tushirish

    Args:
        bot_id: Bot ID
        worker_count: Worker soni (default 1)
    """
    try:
        await worker_pool.start_worker(bot_id, worker_count=worker_count)
        return {"status": "started", "bot_id": bot_id, "workers": worker_count}
    except Exception as e:
        logger.error(f"Start worker error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop/{bot_id}")
async def stop_worker(bot_id: int):
    """
    Bot uchun worker to'xtatish

    Args:
        bot_id: Bot ID
    """
    try:
        await worker_pool.stop_worker(bot_id)
        return {"status": "stopped", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Stop worker error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{bot_id}")
async def get_worker_status(bot_id: int):
    """
    Worker statusini olish

    Args:
        bot_id: Bot ID
    """
    try:
        status = await worker_pool.get_worker_status(bot_id)
        return {"bot_id": bot_id, **status}
    except Exception as e:
        logger.error(f"Get worker status error: {e}")
        return {"bot_id": bot_id, "status": "error", "error": str(e)}


@router.get("/status")
async def get_all_workers_status():
    """Barcha worker statuslarini olish"""
    try:
        status = await worker_pool.get_all_status()
        return {"workers": status, "total": len(status)}
    except Exception as e:
        logger.error(f"Get all workers status error: {e}")
        return {"workers": {}, "total": 0, "error": str(e)}


@router.get("/queue/length/{bot_id}")
async def get_queue_length(bot_id: int):
    """
    Queue uzunligini olish

    Args:
        bot_id: Bot ID
    """
    try:
        if not redis_client.is_connected():
            return {"bot_id": bot_id, "queue_length": 0, "redis_connected": False}

        length = await redis_client.get_queue_length(bot_id)
        return {"bot_id": bot_id, "queue_length": length, "redis_connected": True}
    except Exception as e:
        logger.error(f"Get queue length error: {e}")
        return {"bot_id": bot_id, "queue_length": 0, "error": str(e)}


@router.post("/restart/{bot_id}")
async def restart_worker(bot_id: int):
    """
    Worker ni qayta ishga tushirish

    Args:
        bot_id: Bot ID
    """
    try:
        # Stop
        await worker_pool.stop_worker(bot_id)
        # Start
        await worker_pool.start_worker(bot_id, worker_count=1)
        return {"status": "restarted", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Restart worker error: {e}")
        raise HTTPException(status_code=500, detail=str(e))