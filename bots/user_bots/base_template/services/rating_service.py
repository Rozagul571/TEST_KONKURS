# bots/user_bots/base_template/services/rating_service.py
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from django_app.core.models import Participant
from asgiref.sync import sync_to_async

class RatingService:

    def __init__(self, competition_id):
        self.competition_id = competition_id

    async def get_rating_text(self, user_id: int):
        """Builds leaderboard text with user rank."""
        # Fetch top 10
        leaderboard = await sync_to_async(list)(
            Participant.objects.filter(competition_id=self.competition_id, is_participant=True)
            .select_related('user')
            .order_by(F('current_points').desc())
            .values('user__username', 'user__full_name', 'current_points')[:10]
        )

        rating_text = "🏆 Top 10 ishtirokchilar:\n\n"
        for index, participant in enumerate(leaderboard, 1):
            username = participant['user__username'] or "Noma'lum"
            full_name = participant['user__full_name'] or ""
            points = participant['current_points']
            rating_text += f"{index}. {full_name} (@{username}) - {points} ball\n"

        # Fetch user rank (ORM)
        user_rank = await sync_to_async(Participant.objects.filter)(
            competition_id=self.competition_id, user__telegram_id=user_id, is_participant=True
        ).annotate(
            rank=Window(expression=RowNumber(), order_by=F('current_points').desc())
        ).values('rank', 'current_points').first()

        if user_rank:
            rating_text += f"\nSizning o'rningiz: {user_rank['rank']}-o‘rin, {user_rank['current_points']} ball"
        else:
            rating_text += "\nSiz hali reytingda emassiz."

        return rating_text