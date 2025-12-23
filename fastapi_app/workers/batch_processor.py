#fastapi_app/workers/batch_processor.py
"""
Batch processor for database operations - TO'G'RILANGAN
"""
import asyncio
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from asgiref.sync import sync_to_async
from django.db import transaction

from shared.redis_client import redis_client
from django_app.core.models import Point, Referral, Participant

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Batch processor for database operations"""

    def __init__(self):
        self.batch_size = 100
        self.running = False

    async def start(self):
        """Start batch processor"""
        if self.running:
            return

        self.running = True
        asyncio.create_task(self._process_loop())
        logger.info("✅ Batch processor started")

    async def stop(self):
        """Stop batch processor"""
        self.running = False
        logger.info("✅ Batch processor stopped")

    async def _process_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Process referrals
                await self._process_referral_batch()

                # Process points
                await self._process_points_batch()

                # Wait before next batch
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(30)

    async def _process_referral_batch(self):
        """Process referral batch"""
        if not redis_client.is_connected():
            logger.warning("Redis not connected, skipping referral batch")
            return

        try:
            # Get referrals from Redis using SYNC method
            key = f"referral_queue:{self._get_bot_id()}"
            referrals = []

            for _ in range(self.batch_size):
                data = redis_client.rpop_sync(key)  # Use sync method
                if not data:
                    break
                referrals.append(json.loads(data))

            if referrals:
                await self._save_referrals_batch(referrals)
                logger.info(f"✅ Processed {len(referrals)} referrals")

        except Exception as e:
            logger.error(f"Process referral batch error: {e}", exc_info=True)

    async def _save_referrals_batch(self, referrals: List[Dict]):
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
                            referrer_id=ref_data.get('referrer_id'),
                            referred_id=ref_data.get('referred_id'),
                            competition_id=ref_data.get('competition_id'),
                            is_premium=ref_data.get('is_premium', False),
                            status='completed',
                            created_at=datetime.now()
                        )
                        referral_objects.append(referral)

                        # Create points for referrer
                        points = ref_data.get('points', 5)
                        if ref_data.get('is_premium'):
                            points *= 2

                        # Get participant
                        participant = Participant.objects.get(
                            user_id=ref_data.get('referrer_id'),
                            competition_id=ref_data.get('competition_id')
                        )

                        point = Point(
                            participant=participant,
                            earned_points=points,
                            reason='referral',
                            details={'referred_id': ref_data.get('referred_id')},
                            created_at=datetime.now()
                        )
                        point_objects.append(point)

                    except Participant.DoesNotExist:
                        logger.warning(f"Participant not found: {ref_data.get('referrer_id')}")
                        continue
                    except Exception as e:
                        logger.error(f"Create referral object error: {e}")
                        continue

                # Bulk create
                if referral_objects:
                    Referral.objects.bulk_create(referral_objects)
                    logger.info(f"Created {len(referral_objects)} referrals")

                if point_objects:
                    Point.objects.bulk_create(point_objects)
                    logger.info(f"Created {len(point_objects)} points")

                # Update participant totals
                for point in point_objects:
                    participant = point.participant
                    participant.current_points += point.earned_points
                    participant.save(update_fields=['current_points'])

                return len(referral_objects)

            count = await _save_batch()
            if count > 0:
                logger.info(f"✅ Saved {count} referrals to database")

        except Exception as e:
            logger.error(f"Save referrals batch error: {e}", exc_info=True)

    async def _process_points_batch(self):
        """Process points batch"""
        if not redis_client.is_connected():
            logger.warning("Redis not connected, skipping points batch")
            return

        try:
            # Get points from Redis using SYNC methods
            pattern = f"points_batch:{self._get_bot_id()}:*"
            keys = redis_client.keys_sync(pattern)  # Use sync method

            for key in keys:
                data = redis_client.get_sync(key)  # Use sync method
                if not data:
                    continue

                points_batch = json.loads(data)
                await self._save_points_batch(points_batch)

                # Delete from Redis
                redis_client.delete_sync(key)  # Use sync method

        except Exception as e:
            logger.error(f"Process points batch error: {e}", exc_info=True)

    async def _save_points_batch(self, points_batch: List[Dict]):
        """Save points batch"""
        try:
            @sync_to_async
            @transaction.atomic
            def _save_batch():
                point_objects = []

                for point_data in points_batch:
                    try:
                        point = Point(
                            participant_id=point_data.get('participant_id'),
                            earned_points=point_data.get('points', 0),
                            reason=point_data.get('reason', 'other'),
                            details=point_data.get('details', {}),
                            created_at=datetime.now()
                        )
                        point_objects.append(point)
                    except Exception as e:
                        logger.error(f"Create point object error: {e}")
                        continue

                if point_objects:
                    Point.objects.bulk_create(point_objects)

                    # Update participant totals
                    for point in point_objects:
                        try:
                            participant = Participant.objects.get(id=point.participant_id)
                            participant.current_points += point.earned_points
                            participant.save(update_fields=['current_points'])
                        except Participant.DoesNotExist:
                            logger.warning(f"Participant {point.participant_id} not found")
                            continue

                return len(point_objects)

            count = await _save_batch()
            if count > 0:
                logger.info(f"✅ Saved {count} points to database")

        except Exception as e:
            logger.error(f"Save points batch error: {e}", exc_info=True)

    def _get_bot_id(self):
        """Get bot ID for current context"""
        # Sizning mantiqingizga qarab o'zgartiring
        return 1  # default bot ID