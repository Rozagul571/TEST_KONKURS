from django.urls import path

from django_app.core.views import panel_view

urlpatterns = [
    path('', panel_view, name='panel'),  # ?bot_id bilan filter
]