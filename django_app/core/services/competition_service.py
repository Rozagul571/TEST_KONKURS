# django_app/core/services/competition_service.py
from asgiref.sync import sync_to_async
from ..models.competition import Competition

class CompetitionService:
    @sync_to_async
    def get_active_competition(self, owner):
        competition = Competition.objects.filter(creator=owner, status='active').first()
        if competition:
            return {
                'id': competition.id,
                'name': competition.name,
                'description': competition.description,
                'rules_text': competition.rules_text,
                'start_at': competition.start_at,
                'end_at': competition.end_at,
                'welcome_image': competition.welcome_image.url if competition.welcome_image else None,
                'channels': [{'id': ch.id, 'channel_username': ch.channel_username} for ch in competition.channels.all()],
                'point_rules': {rule.action_type: rule.points for rule in competition.point_rules.all()},
                'prizes': [{'place': p.place, 'prize_name': p.prize_name, 'prize_amount': p.prize_amount, 'type': p.type} for p in competition.prize_set.all()],
            }
        return None