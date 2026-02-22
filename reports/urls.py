from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_dashboard, name='dashboard'),
    path('generate/', views.report_generate, name='report_generate'),
    path('generate/<str:date_str>/', views.report_generate, name='report_view'),
    path('pdf/<str:date_str>/', views.report_pdf, name='report_pdf'),
    path('pdf/briefing/<str:date_str>/', views.briefing_pdf, name='briefing_pdf'),
    path('pdf/qa/<str:date_str>/', views.qa_pdf, name='qa_pdf'),
    path('pdf/incidents/<str:date_str>/', views.incidents_pdf, name='incidents_pdf'),
]
