import asyncio
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from asgiref.sync import sync_to_async
from django.db import transaction

from shared.redis_client import redis_client
from django_app.core.models import Point, Referral, Participant
from django_app.core.services.point_calculator import PointCalculator

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Batch processor for database operations"""

    def __init__(self):
        self.batch_size = 100  # Process 100 records at once
        self.running = False

    async def start(self):
        """Start batch processor"""
        self.running = True
        asyncio.create_task(self._process_loop())
        logger.info("Batch processor started")

    async def stop(self):
        """Stop batch processor"""
        self.running = False
        logger.info("Batch processor stopped")

    async def _process_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Process referrals
                await self._process_referral_batch()

                # Process points
                await self._process_points_batch()

                # Cleanup old cache
                await self._cleanup_cache()

                # Sleep between batches
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(10)

    async def _process_referral_batch(self):
        """Process referral batch"""
        if not redis_client.is_connected():
            return

        try:
            # Get referrals from all bot queues
            pattern = "referral_queue:*"
            keys = redis_client.client.keys(pattern)

            for key in keys:
                bot_id = int(key.split(":")[-1])

                # Process up to batch_size referrals
                referrals = []
                for _ in range(self.batch_size):
                    data = redis_client.client.rpop(key)
                    if not data:
                        break
                    referrals.append(json.loads(data))

                if referrals:
                    await self._save_referrals_batch(referrals, bot_id)

        except Exception as e:
            logger.error(f"Process referral batch error: {e}")

    async def _save_referrals_batch(self, referrals: List[Dict], bot_id: int):
        """Save referrals in batch"""
        try:
            @sync_to_async
            @transaction.atomic
            def _save_batch():
                referral_objects = []
                point_objects = []

                for ref_data in referrals:
                    try:
                        # Create referral
                        referral = Referral(
                            referrer_id=ref_data['referrer_id'],
                            referred_id=ref_data['referred_id'],
                            competition_id=bot_id,
                            is_premium=ref_data.get('premium', False),
                            created_at=datetime.fromisoformat(ref_data['timestamp'])
                        )
                        referral_objects.append(referral)

                        # Create points for referrer
                        participant = Participant.objects.get(
                            user__telegram_id=ref_data['referrer_id'],
                            competition_id=bot_id
                        )

                        points = 5  # Base referral points
                        if ref_data.get('premium'):
                            points *= 2  # Double for premium referrals

                        point = Point(
                            participant=participant,
                            earned_points=points,
                            reason='referral',
                            created_at=datetime.now()
                        )
                        point_objects.append(point)

                    except Exception as e:
                        logger.error(f"Create referral object error: {e}")
                        continue

                # Bulk create
                if referral_objects:
                    Referral.objects.bulk_create(referral_objects)

                if point_objects:
                    Point.objects.bulk_create(point_objects)

                # Update participant totals
                participant_ids = list(set([p.participant_id for p in point_objects]))
                for participant_id in participant_ids:
                    participant_points = sum(
                        p.earned_points for p in point_objects
                        if p.participant_id == participant_id
                    )

                    participant = Participant.objects.get(id=participant_id)
                    participant.current_points += participant_points
                    participant.save(update_fields=['current_points'])

            await _save_batch()
            logger.info(f"Saved {len(referrals)} referrals for bot {bot_id}")

        except Exception as e:
            logger.error(f"Save referrals batch error: {e}")

    async def _process_points_batch(self):
        """Process points batch from Redis"""
        if not redis_client.is_connected():
            return

        try:
            pattern = "points_batch:*"
            keys = redis_client.client.keys(pattern)

            for key in keys:
                bot_id = int(key.split(":")[-1])

                # Get batch
                data = redis_client.client.get(key)
                if not data:
                    continue

                points_batch = json.loads(data)

                # Save to database
                await self._save_points_batch(points_batch, bot_id)

                # Delete from Redis
                redis_client.client.delete(key)

        except Exception as e:
            logger.error(f"Process points batch error: {e}")

    async def _cleanup_cache(self):
        """Cleanup old cache entries"""
        if not redis_client.is_connected():
            return

        try:
            # Remove old user states (older than 1 hour)
            pattern = "user_state:*"
            keys = redis_client.client.keys(pattern)

            for key in keys:
                # Implementation depends on your TTL strategy
                pass

        except Exception as e:
            logger.error(f"Cleanup cache error: {e}")