from django.contrib import admin
from django.urls import path, include
from core.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('projects/', include('projects.urls')),
    path('qa/', include('qa.urls')),
    path('briefing/', include('briefing.urls')),
    path('monitoring/', include('monitoring.urls')),
    path('planning/', include('planning.urls')),
    path('reports/', include('reports.urls')),
]
