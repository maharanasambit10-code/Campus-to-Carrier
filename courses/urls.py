from django.urls import path
from . import views

urlpatterns = [
    # ── Learning Hub ───────────────────────────────────────────────────────────
    path('',                                   views.learning_hub,          name='course_list'),        # legacy name kept
    path('hub/',                               views.learning_hub,          name='learning_hub'),
    path('hub/progress/',                      views.hub_my_progress,       name='hub_my_progress'),
    path('hub/<slug:course_slug>/',            views.hub_course_detail,     name='hub_course_detail'),
    path('hub/<slug:course_slug>/enroll/',     views.enroll_course,         name='enroll_course'),
    path('hub/<slug:course_slug>/lesson/<int:lesson_id>/',          views.hub_lesson,            name='hub_lesson'),
    path('hub/<slug:course_slug>/lesson/<int:lesson_id>/complete/', views.mark_lesson_complete,  name='mark_lesson_complete'),
    path('hub/<slug:course_slug>/quiz/',                             views.hub_quiz,              name='hub_quiz'),
    path('hub/<slug:course_slug>/quiz/submit/',                      views.hub_quiz_submit,       name='hub_quiz_submit'),
    path('hub/<slug:course_slug>/quiz/result/<int:attempt_id>/',     views.hub_quiz_result,       name='hub_quiz_result'),
    path('hub/certificate/<uuid:cert_uuid>/', views.hub_certificate,        name='hub_certificate'),

    # ── Legacy course URLs (still work) ────────────────────────────────────────
    path('applications/',                      views.course_applications,   name='course_applications'),
    path('<int:course_id>/',                   views.course_detail,         name='course_detail'),
    path('<int:course_id>/apply/',             views.apply_course,          name='apply_course'),
]
