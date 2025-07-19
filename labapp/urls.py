from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_form, name='student_form'),  # Home page
    path('dashboard/<str:action>/', views.component_dashboard, name='dashboard'),
    path('issue/', views.issue_form, name='issue_form'),
    path('return/', views.return_form, name='return_form'),
    path('success/', views.success, name='success'),
    path('admin-report/', views.admin_report, name='admin_report'),
    path('issue_auto/', views.live_auto_issue, name='issue_auto'),
    path('return_auto/', views.live_auto_return, name='return_auto'),
]
