from django.urls import path

from . import views

urlpatterns = [
    path('resume/', views.resume_analysis, name='resume_analysis'),
]
