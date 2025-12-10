# django_app/core/tasks.py
from celery import shared_task
from django_app.core.models import Point, Referral, Participant
import redis
import json
import logging

logger = logging.getLogger(__name__)
r = redis.Redis(host='localhost', port=6379, db=0)

@shared_task
def batch_save_data(bot_id: int):
    """Redis dan DB ga ma'lumotlarni ko‘chiradi"""
    try:
        # Referral larni olish
        referrals = r.lrange(f"referrals:{bot_id}", 0, -1)
        referral_objs = []
        for ref in referrals:
            data = json.loads(ref)
            referral_objs.append(
                Referral(
                    referrer_id=data['referrer'],
                    referred_id=data['referred'],
                    competition_id=data['competition']
                )
            )
        if referral_objs:
            Referral.objects.bulk_create(referral_objs)
            r.delete(f"referrals:{bot_id}")

        # Ballarni olish
        keys = r.keys(f"user_points:{bot_id}:*")
        point_objs = []
        for key in keys:
            user_id = int(key.decode().split(":")[-1])
            points = int(r.get(key) or 0)
            participant = Participant.objects.get(user_id=user_id, competition_id=bot_id)
            point_objs.append(Point(participant=participant, earned_points=points, reason='total'))
        if point_objs:
            Point.objects.bulk_create(point_objs)
            r.delete(*keys)

        logger.info(f"Bot {bot_id} uchun batch saqlash muvaffaqiyatli")
    except Exception as e:
        logger.error(f"Batch saqlash xatosi: {e}")