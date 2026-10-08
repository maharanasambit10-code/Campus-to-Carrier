from django.urls import path
from . import views

urlpatterns = [
    # Product 01: Career Flight Simulator
    path('simulator/', views.simulator_catalog, name='simulator_catalog'),
    path('simulator/<slug:slug>/', views.simulator_challenge_detail, name='simulator_challenge_detail'),
    path('simulator/<slug:slug>/submit/', views.simulator_submit, name='simulator_submit'),
    path('simulator/result/<int:submission_id>/', views.simulator_result, name='simulator_result'),

    # Product 02: Opportunity Compiler
    path('compiler/', views.opportunity_compiler_home, name='opportunity_compiler_home'),
    path('compiler/run/', views.opportunity_compiler_run, name='opportunity_compiler_run'),
    path('compiler/session/<int:session_id>/', views.opportunity_compiler_detail, name='opportunity_compiler_detail'),
    path('compiler/session/<int:session_id>/task/<int:task_index>/toggle/', views.opportunity_toggle_task, name='opportunity_toggle_task'),
    path('compiler/proof-brief/<str:token>/', views.opportunity_proof_brief, name='opportunity_proof_brief'),

    # Product 03: Proof Passport
    path('passport/', views.proof_passport_dashboard, name='proof_passport_dashboard'),
    path('passport/view/<str:token>/', views.proof_passport_public_view, name='proof_passport_public_view'),
    path('passport/artifact/add/', views.proof_passport_add_artifact, name='proof_passport_add_artifact'),
    path('passport/peer-review/add/', views.proof_passport_add_peer_review, name='proof_passport_add_peer_review'),
    path('passport/settings/update/', views.proof_passport_update_settings, name='proof_passport_update_settings'),
]
