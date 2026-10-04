
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('applications/', views.student_applications, name='student_applications'),
    path('profile/', views.student_profile, name='student_profile'),
    path('career-match/', views.career_match, name='career_match'),
    path('resume/download/', views.resume_download, name='resume_download'),
    path('profile/add-skill/', views.add_skill, name='add_skill'),
    path('profile/skill/<int:skill_id>/update/', views.update_skill, name='update_skill'),
    path('profile/skill/<int:skill_id>/delete/', views.delete_skill, name='delete_skill'),
    path('profile/project/add/', views.save_project, name='save_project'),
    path('profile/project/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('profile/project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('profile/recruiter-preview/', views.recruiter_preview, name='recruiter_preview'),
    path('profile/certification/add/', views.save_certification, name='save_certification'),
    path('profile/certification/<int:certification_id>/edit/', views.edit_certification, name='edit_certification'),
    path('profile/certification/<int:certification_id>/delete/', views.delete_certification, name='delete_certification'),
    path('profile/experience/add/', views.save_internship, name='save_internship'),
    path('profile/experience/<int:internship_id>/edit/', views.edit_internship, name='edit_internship'),
    path('profile/experience/<int:internship_id>/delete/', views.delete_internship, name='delete_internship'),
    path('profile/achievement/add/', views.save_achievement, name='save_achievement'),
    path('profile/achievement/<int:achievement_id>/edit/', views.edit_achievement, name='edit_achievement'),
    path('profile/achievement/<int:achievement_id>/delete/', views.delete_achievement, name='delete_achievement'),
]
