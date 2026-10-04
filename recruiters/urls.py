
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('jobs/create/', views.recruiter_job_create, name='recruiter_job_create'),
    path('jobs/<int:job_id>/edit/', views.recruiter_job_edit, name='recruiter_job_edit'),
    path('applications/<int:application_id>/status/', views.recruiter_application_status, name='recruiter_application_status'),
]
