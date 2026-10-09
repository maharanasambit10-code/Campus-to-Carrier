from django.urls import path
from . import views

urlpatterns = [
    # Hackathon Demo: 3-Minute "Wow" Journey (Slides 9 & 13)
    path('demo/', views.hackathon_demo_journey, name='hackathon_demo'),
    path('wow-journey/', views.hackathon_demo_journey, name='wow_journey'),

    # Engine 01: Role Decoder (Slides 4 & 9)
    path('role-decoder/', views.role_decoder_view, name='role_decoder'),

    # Engine 02: Proof Miner (Slides 4, 6 & 10)
    path('proof-miner/', views.proof_miner_view, name='proof_miner'),
    path('api/proof/parse-github/', views.api_parse_github_repo, name='api_parse_github'),

    # Engine 03: Readiness Score & Evidence Trail (Slides 1, 4 & 6)
    path('readiness-score/', views.readiness_score_view, name='readiness_score'),

    # Engine 04: Action Coach (Slide 4)
    path('action-coach/', views.action_coach_view, name='action_coach'),

    # AI Feature: The 15-Minute Role Mission (Slide 5)
    path('role-mission/', views.role_mission_workspace, name='role_mission_default'),
    path('role-mission/<slug:slug>/', views.role_mission_workspace, name='role_mission_workspace'),
    path('role-mission/result/<int:submission_id>/', views.role_mission_result, name='role_mission_result'),

    # College Impact: Live Readiness Radar (Slide 7)
    path('readiness-radar/', views.college_readiness_radar_view, name='college_readiness_radar'),
    path('readiness-radar/launch-intervention/', views.college_launch_intervention, name='college_launch_intervention'),

    # Recruiter View: Shortlist by Proof (Slide 8)
    path('recruiter/proof-shortlist/', views.recruiter_proof_shortlist_view, name='recruiter_proof_shortlist'),
    path('recruiter/proof-shortlist/<int:candidate_id>/toggle/', views.recruiter_toggle_shortlist, name='recruiter_toggle_shortlist'),
    path('recruiter/proof-shortlist/<int:candidate_id>/send-mission/', views.recruiter_send_mission, name='recruiter_send_mission'),

    # Advanced Ecosystem & Hackathon Features
    path('skill-graph/', views.career_skill_graph_view, name='career_skill_graph'),
    path('interview-arena/', views.interview_arena_view, name='interview_arena'),
    path('interview-arena/submit/', views.interview_arena_submit, name='interview_arena_submit'),
    path('placement-risk/', views.placement_risk_early_warning_view, name='placement_risk_early_warning'),
    path('placement-risk/dispatch/', views.placement_risk_dispatch_intervention, name='placement_risk_dispatch'),
    path('next-best-action/', views.personalized_improvement_view, name='personalized_improvement'),
    path('ecosystem/', views.ecosystem_hub_view, name='ecosystem_hub'),
    path('pitch/', views.final_hackathon_pitch_view, name='final_hackathon_pitch'),

    # Career Flight Simulator
    path('simulator/', views.simulator_catalog, name='simulator_catalog'),
    path('simulator/<slug:slug>/', views.simulator_challenge_detail, name='simulator_challenge_detail'),
    path('simulator/<slug:slug>/submit/', views.simulator_submit, name='simulator_submit'),
    path('simulator/result/<int:submission_id>/', views.simulator_result, name='simulator_result'),

    # Opportunity Compiler
    path('compiler/', views.opportunity_compiler_home, name='opportunity_compiler_home'),
    path('compiler/run/', views.opportunity_compiler_run, name='opportunity_compiler_run'),
    path('compiler/session/<int:session_id>/', views.opportunity_compiler_detail, name='opportunity_compiler_detail'),
    path('compiler/session/<int:session_id>/task/<int:task_index>/toggle/', views.opportunity_toggle_task, name='opportunity_toggle_task'),
    path('compiler/proof-brief/<str:token>/', views.opportunity_proof_brief, name='opportunity_proof_brief'),

    # Proof Passport
    path('passport/', views.proof_passport_dashboard, name='proof_passport_dashboard'),
    path('passport/view/<str:token>/', views.proof_passport_public_view, name='proof_passport_public_view'),
    path('passport/artifact/add/', views.proof_passport_add_artifact, name='proof_passport_add_artifact'),
    path('passport/peer-review/add/', views.proof_passport_add_peer_review, name='proof_passport_add_peer_review'),
    path('passport/settings/update/', views.proof_passport_update_settings, name='proof_passport_update_settings'),

    # 12 Killer Unique Features for Campus to Career
    path('unique-features/', views.innovation_suite_view, name='innovation_suite'),
    path('unique-features/taskbar/', views.innovation_suite_view, name='innovation_taskbar'),
    path('api/unique-features/<str:feature_name>/', views.api_feature_interaction, name='api_feature_interaction'),
]

