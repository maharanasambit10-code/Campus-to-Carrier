from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('<int:job_id>/', views.job_detail, name='job_detail'),
    path('<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('saved/', views.saved_jobs_list, name='saved_jobs_list'),
    path('company/<int:company_id>/connect/', views.connect_company, name='job_connect_company'),
    path('api/match/', views.api_resume_match, name='api_resume_match'),
    path('api/save/<int:job_id>/', views.toggle_save_job, name='toggle_save_job'),
    path('api/company/<int:company_id>/', views.api_company_details, name='api_company_details'),
]
