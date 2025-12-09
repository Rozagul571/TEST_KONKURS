# # django_app/core/admin/site.py
# from django.contrib.admin import AdminSite
# from django.http import HttpRequest
# from django.db.models import Count
# from django.utils import timezone
# import json
#
# class CustomAdminSite(AdminSite):
#     """Custom admin site. Vazifasi: Admin panel dizayn va filtrlarini customize qilish. Misol: Superadmin uchun full access, oddiy admin uchun faqat o'z konkursi."""
#     site_header = "🏆 Konkurs Platformasi"
#     site_title = "Konkurs Admin"
#     index_title = "Dashboard"
#
#     def get_app_list(self, request: HttpRequest):
#         app_list = super().get_app_list(request)
#         if request.user.is_superuser:
#             return app_list
#         filtered_app_list = []
#         for app in app_list:
#             if app['app_label'] == 'core':
#                 filtered_models = [m for m in app['models'] if m['object_name'] in ['Competition', 'Channel', 'PointRule', 'Prize', 'Participant']]
#                 if filtered_models:
#                     app['models'] = filtered_models
#                     filtered_app_list.append(app)
#         return filtered_app_list
#
#     def index(self, request, extra_context=None):
#         extra_context = extra_context or {}
#         from ..models.competition import Competition, CompetitionStatus
#         from ..models.bot import BotSetUp, BotStatus
#         from ..models.participant import Participant
#         from ..models.user import User
#         stats = {
#             'total_competitions': Competition.objects.count(),
#             'active_competitions': Competition.objects.filter(status=CompetitionStatus.ACTIVE).count(),
#             'total_bots': BotSetUp.objects.count(),
#             'running_bots': BotSetUp.objects.filter(status=BotStatus.RUNNING).count(),
#             'total_participants': Participant.objects.count(),
#             'total_users': User.objects.count(),
#         }
#         top_competitions = Competition.objects.annotate(participants_count=Count('participants')).order_by('-participants_count')[:5]
#         recent_bots = BotSetUp.objects.select_related('owner').order_by('-created_at')[:5]
#         chart_data = self.get_chart_data()
#         extra_context.update({
#             'stats': stats,
#             'top_competitions': top_competitions,
#             'recent_bots': recent_bots,
#             'chart_data': json.dumps(chart_data),
#         })
#         return super().index(request, extra_context)
#
#     def get_chart_data(self):
#         from ..models.competition import Competition
#         from ..models.participant import Participant
#         from django.db.models.functions import TruncDay
#         seven_days_ago = timezone.now() - timezone.timedelta(days=7)
#         competitions_by_day = list(Competition.objects.filter(created_at__gte=seven_days_ago).annotate(day=TruncDay('created_at')).values('day').annotate(count=Count('id')).order_by('day'))
#         participants_by_day = list(Participant.objects.filter(joined_at__gte=seven_days_ago).annotate(day=TruncDay('joined_at')).values('day').annotate(count=Count('id')).order_by('day'))
#         return {'competitions': competitions_by_day, 'participants': participants_by_day}
#
# admin_site = CustomAdminSite(name='custom_admin')