from django.urls import path
from . import views

app_name = 'qa'

urlpatterns = [
    path('', views.qa_dashboard, name='dashboard'),
    path('checklist/new/', views.qa_checklist_create, name='checklist_create'),
    path('checklist/<int:pk>/', views.qa_checklist_detail, name='checklist_detail'),
    path('inspection/<int:pk>/', views.inspection_detail, name='inspection_detail'),
    path('ncr/', views.ncr_list, name='ncr_list'),
]
