# fastapi_app/api/routes/worker_api.py
"""
Worker API endpoints - TO'G'RILANGAN
"""
from fastapi import APIRouter, HTTPException
import logging
from shared.redis_client import redis_client
from fastapi_app.workers.bot_worker import worker_pool

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/start/{bot_id}")
async def start_worker(bot_id: int):
    """Start worker for bot"""
    try:
        await worker_pool.start_worker(bot_id, worker_count=1)
        return {"status": "started", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Start worker error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop/{bot_id}")
async def stop_worker(bot_id: int):
    """Stop worker for bot"""
    try:
        await worker_pool.stop_worker(bot_id)
        return {"status": "stopped", "bot_id": bot_id}
    except Exception as e:
        logger.error(f"Stop worker error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{bot_id}")
async def get_worker_status(bot_id: int):
    """Get worker status"""
    try:
        status = await worker_pool.get_worker_status(bot_id)
        return {"bot_id": bot_id, "status": status}
    except Exception as e:
        logger.error(f"Get worker status error: {e}")
        return {"bot_id": bot_id, "status": "error", "error": str(e)}


@router.get("/queue/length/{bot_id}")
async def get_queue_length(bot_id: int):
    """Get queue length for bot"""
    try:
        if not redis_client.is_connected():
            return {"bot_id": bot_id, "queue_length": 0}

        queue_key = f"bot_queue:{bot_id}"
        length = redis_client.client.llen(queue_key)
        return {"bot_id": bot_id, "queue_length": length}
    except Exception as e:
        logger.error(f"Get queue length error: {e}")
        return {"bot_id": bot_id, "queue_length": 0}