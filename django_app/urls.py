from django.conf.urls.static import static
from .settings import MEDIA_URL, MEDIA_ROOT
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel/', include('django_app.core.urls')),
]+ static(MEDIA_URL, document_root=MEDIA_ROOT)