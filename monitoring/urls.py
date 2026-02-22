from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('', views.monitoring_dashboard, name='dashboard'),
    path('locations/', views.location_map, name='location_map'),
    path('team/<int:pk>/', views.team_detail, name='team_detail'),
]
