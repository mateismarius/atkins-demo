from django.urls import path
from . import views

app_name = 'planning'

urlpatterns = [
    path('', views.planning_dashboard, name='dashboard'),
    path('plan/create/', views.create_plan, name='create_plan'),
    path('plan/<int:pk>/', views.shift_plan_detail, name='plan_detail'),
    path('plan/<int:pk>/copy/', views.copy_plan, name='copy_plan'),
    path('plan/<int:pk>/publish/', views.toggle_publish, name='toggle_publish'),
    path('plan/<int:pk>/pdf/', views.plan_pdf, name='plan_pdf'),
    path('plan/<int:plan_pk>/add/', views.add_assignment, name='add_assignment'),
    path('assignment/<int:pk>/edit/', views.edit_assignment, name='edit_assignment'),
    path('assignment/<int:pk>/delete/', views.delete_assignment, name='delete_assignment'),
    path('assignment/<int:pk>/status/', views.update_assignment_status, name='update_status'),
    path('resources/', views.resource_list, name='resources'),
]
