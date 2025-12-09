# bots/user_bots/base_template/services/rating_service.py
from asgiref.sync import sync_to_async
from django.db.models import Window, F
from django.db.models.functions import RowNumber
from django_app.core.models.participant import Participant

class RatingService:
    """Rating servisi. Vazifasi: Reyting text yaratish. Misol: get_rating_text - top 10 va user o'rni."""
    def __init__(self, competition_data):
        self.competition_data = competition_data

    @sync_to_async
    def get_rating_text(self, participant):
        leaderboard = Participant.objects.filter(competition_id=self.competition_data['id'], is_participant=True).select_related('user').order_by('-current_points')[:10]
        rating_text = "🏆 <b>Reyting (TOP 10):</b>\n\n"
        for i, p in enumerate(leaderboard, 1):
            username = f"@{p.user.username}" if p.user.username else ""
            full_name = p.user.full_name or "Noma'lum"
            display = f"{full_name} {username}".strip()
            medal = self._get_medal(i)
            rating_text += f"{medal} {i}-o'rin: {display} — {p.current_points} ball\n"
        # User place: Window bilan
        all_participants = Participant.objects.filter(
            competition_id=self.competition_data['id'],
            is_participant=True
        ).annotate(
            rank=Window(expression=RowNumber(), order_by=F('current_points').desc())
        ).select_related('user')
        user_place = None
        for p in all_participants:
            if p.id == participant.id:
                user_place = p.rank
                break
        if user_place:
            rating_text += f"\n👤 <b>Siz:</b> {user_place}-o'rindasiz — {participant.current_points} ball"
        else:
            rating_text += f"\n👤 <b>Siz:</b> Reytingda emas — {participant.current_points} ball"
        return rating_text

    def _get_medal(self, i):
        medals = {1: '🥇', 2: '🥈', 3: '🥉'}
        return medals.get(i, '🏅')

# from asgiref.sync import sync_to_async
# from django.db.models import Window, F, RowNumber
# from django.db.models.functions import RowNumber as RN
# from django_app.core.models.participant import Participant
#
# class RatingService:
#     """Rating servisi. Vazifasi: Reyting text yaratish. Misol: get_rating_text - top 10 va user o'rni. O'ZGARTIRILGAN: ORM bilan optimizatsiya."""
#     def __init__(self, competition_data):
#         self.competition_data = competition_data
#
#     @sync_to_async
#     def get_rating_text(self, participant):
#         # O'ZGARTIRILGAN: ORM bilan top-10, annotate bilan user place (Window RowNumber)
#         from django.db.models import Desc
#         leaderboard = Participant.objects.filter(
#             competition_id=self.competition_data['id'],
#             is_participant=True
#         ).select_related('user').order_by(Desc('current_points'))[:10]
#
#         rating_text = "🏆 <b>Reyting (TOP 10):</b>\n\n"
#         for i, p in enumerate(leaderboard, 1):
#             username = f"@{p.user.username}" if p.user.username else ""
#             full_name = p.user.full_name or "Noma'lum"
#             display = f"{full_name} {username}".strip()
#             medal = self._get_medal(i)
#             rating_text += f"{medal} {i}-o'rin: {display} — {p.current_points} ball\n"
#
#         # User place: Window bilan butun reyting rank hisoblash
#         all_participants = Participant.objects.filter(
#             competition_id=self.competition_data['id'],
#             is_participant=True
#         ).annotate(
#             rank=Window(
#                 expression=RN(),
#                 order_by=Desc(F('current_points'))
#             )
#         ).select_related('user')
#         user_place = None
#         for p in all_participants:
#             if p.id == participant.id:
#                 user_place = p.rank
#                 break
#         if user_place and user_place <= 10:
#             rating_text += f"\n👤 <b>Siz:</b> {user_place}-o'rindasiz — {participant.current_points} ball"
#         else:
#             rating_text += f"\n👤 <b>Siz:</b> Reytingda emas — {participant.current_points} ball"
#         return rating_text
#
#     def _get_medal(self, place):
#         medals = {1: '🥇', 2: '🥈', 3: '🥉'}
#         return medals.get(place, '🏅')
    #
    # def _get_medal(self, place):
    #     if place == 1: return "🏅"
    #     if place == 2: return "🥈"
    #     if place == 3: return "🥉"
    #     return "•"