# django_app/core/admin_dashboard/urls.py
"""
Dashboard URLs
"""
from django.urls import path
from .views import DashboardView, run_bot_view

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    # path('run-bot/<int:competition_id>/', run_bot_view, name='run-bot'),
]
