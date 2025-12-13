from fastapi import APIRouter, BackgroundTasks, HTTPException
import logging
import asyncio
from typing import List, Dict, Any
from shared.redis_client import redis_client
from fastapi_app.workers.bot_worker import BotWorkerPool

logger = logging.getLogger(__name__)
router = APIRouter()
worker_pool = BotWorkerPool()


@router.post("/start/{bot_id}")
async def start_worker(bot_id: int, background_tasks: BackgroundTasks):
    """Start worker for specific bot"""
    try:
        await worker_pool.start_worker(bot_id)
        return {"status": "started", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Start worker error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop/{bot_id}")
async def stop_worker(bot_id: int):
    """Stop worker for specific bot"""
    try:
        await worker_pool.stop_worker(bot_id)
        return {"status": "stopped", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Stop worker error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{bot_id}")
async def get_worker_status(bot_id: int):
    """Get worker status"""
    status = await worker_pool.get_worker_status(bot_id)
    return {"bot_id": bot_id, "status": status}


@router.get("/stats/{bot_id}")
async def get_worker_stats(bot_id: int):
    """Get worker statistics"""
    stats = await worker_pool.get_worker_stats(bot_id)
    return {"bot_id": bot_id, "stats": stats}


@router.get("/queue/length/{bot_id}")
async def get_queue_length(bot_id: int):
    """Get queue length for bot"""
    if not redis_client.is_connected():
        return {"bot_id": bot_id, "queue_length": 0}

    try:
        queue_key = f"bot_queue:{bot_id}"
        length = redis_client.client.llen(queue_key)
        return {"bot_id": bot_id, "queue_length": length}
    except Exception as e:
        logger.error(f"Get queue length error: {e}")
        return {"bot_id": bot_id, "queue_length": 0}