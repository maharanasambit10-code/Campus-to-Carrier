from django.urls import path

from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('applications/', views.course_applications, name='course_applications'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/apply/', views.apply_course, name='apply_course'),
]
