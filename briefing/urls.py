from django.urls import path
from . import views

app_name = 'briefing'

urlpatterns = [
    path('', views.briefing_dashboard, name='dashboard'),
    path('form/new/', views.prebriefing_form_create, name='form_create'),
    path('form/<int:pk>/', views.prebriefing_form_detail, name='form_detail'),
    path('session/<int:pk>/', views.briefing_detail, name='briefing_detail'),
    path('overview/', views.briefing_overview, name='overview'),
    path('overview/<str:date_str>/', views.briefing_overview, name='overview_date'),
]
