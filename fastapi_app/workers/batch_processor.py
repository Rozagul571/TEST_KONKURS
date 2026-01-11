# fastapi_app/workers/batch_processor.py
"""
Batch Processor - SIMPLIFIED
Redis metodlari muammosi tufayli soddalashtirildi
Hozircha batch processing kerak emas - to'g'ridan-to'g'ri process qilinadi
"""
import logging
import asyncio

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Simplified batch processor - currently disabled"""

    def __init__(self):
        self.running = False

    async def start(self):
        """Start - hozircha hech narsa qilmaydi"""
        self.running = True
        logger.info("✅ Batch processor initialized (simplified mode)")

    async def stop(self):
        """Stop"""
        self.running = False
        logger.info("Batch processor stopped")

    async def _process_loop(self):
        """Process loop - disabled"""
        pass
