from django.urls import path
from . import views

urlpatterns = [
    path('', views.interview_list, name='interview_list'),
    path('mock/', views.ai_mock_interview, name='ai_mock_interview'),
    path('mock/api/start/', views.api_start_mock_interview, name='api_start_mock_interview'),
    path('mock/api/turn/', views.api_aria_turn, name='api_aria_turn'),
    path('mock/api/tts/', views.api_synthesize_tts, name='api_synthesize_tts'),
    path('mock/api/avatar-session/', views.api_avatar_session, name='api_avatar_session'),
    path('mock/api/finish/', views.api_finish_mock_interview, name='api_finish_mock_interview'),
    path('mock/report/<int:session_id>/', views.mock_interview_report, name='mock_interview_report'),
    path('schedule/<int:application_id>/', views.schedule_interview, name='schedule_interview'),
]