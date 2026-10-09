from django.urls import path
from . import views

urlpatterns = [
    # Platform Walkthrough & Product Tour
    path('tour/', views.hackathon_demo_journey, name='hackathon_demo'),
    path('walkthrough/', views.hackathon_demo_journey),
    path('demo/', views.hackathon_demo_journey),
    path('wow-journey/', views.hackathon_demo_journey, name='wow_journey'),

    # Career Role Intelligence & Skills Analysis
    path('role-decoder/', views.role_decoder_view, name='role_decoder'),

    # Proof Miner & Repository Verification
    path('proof-miner/', views.proof_miner_view, name='proof_miner'),
    path('api/proof/parse-github/', views.api_parse_github_repo, name='api_parse_github'),

    # Career Readiness Scoring & Evidence Tracking
    path('readiness-score/', views.readiness_score_view, name='readiness_score'),

    # Career Action Coach
    path('action-coach/', views.action_coach_view, name='action_coach'),

    # Workplace Role Challenge & Simulations
    path('role-mission/', views.role_mission_workspace, name='role_mission_default'),
    path('role-mission/<slug:slug>/', views.role_mission_workspace, name='role_mission_workspace'),
    path('role-mission/result/<int:submission_id>/', views.role_mission_result, name='role_mission_result'),

    # Institutional Readiness & Analytics Command Center
    path('readiness-radar/', views.college_readiness_radar_view, name='college_readiness_radar'),
    path('readiness-radar/launch-intervention/', views.college_launch_intervention, name='college_launch_intervention'),

    # Enterprise Recruiter Evidence Shortlisting
    path('recruiter/proof-shortlist/', views.recruiter_proof_shortlist_view, name='recruiter_proof_shortlist'),
    path('recruiter/proof-shortlist/<int:candidate_id>/toggle/', views.recruiter_toggle_shortlist, name='recruiter_toggle_shortlist'),
    path('recruiter/proof-shortlist/<int:candidate_id>/send-mission/', views.recruiter_send_mission, name='recruiter_send_mission'),

    # Skill Graph, Assessment Arena & Career Intelligence
    path('skill-graph/', views.career_skill_graph_view, name='career_skill_graph'),
    path('interview-arena/', views.interview_arena_view, name='interview_arena'),
    path('interview-arena/submit/', views.interview_arena_submit, name='interview_arena_submit'),
    path('placement-risk/', views.placement_risk_early_warning_view, name='placement_risk_early_warning'),
    path('placement-risk/dispatch/', views.placement_risk_dispatch_intervention, name='placement_risk_dispatch'),
    path('next-best-action/', views.personalized_improvement_view, name='personalized_improvement'),
    path('ecosystem/', views.ecosystem_hub_view, name='ecosystem_hub'),
    path('vision/', views.final_hackathon_pitch_view, name='final_hackathon_pitch'),
    path('pitch/', views.final_hackathon_pitch_view),

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

    # Verified Proof Passport
    path('passport/', views.proof_passport_dashboard, name='proof_passport_dashboard'),
    path('passport/view/<str:token>/', views.proof_passport_public_view, name='proof_passport_public_view'),
    path('passport/artifact/add/', views.proof_passport_add_artifact, name='proof_passport_add_artifact'),
    path('passport/peer-review/add/', views.proof_passport_add_peer_review, name='proof_passport_add_peer_review'),
    path('passport/settings/update/', views.proof_passport_update_settings, name='proof_passport_update_settings'),

    # Career Innovation Suite & Advanced Verification Modules
    path('innovations/', views.innovation_suite_view, name='innovation_suite'),
    path('innovations/dock/', views.innovation_suite_view, name='innovation_taskbar'),
    path('suite/', views.innovation_suite_view),
    path('unique-features/', views.innovation_suite_view),
    path('unique-features/taskbar/', views.innovation_suite_view),
    path('api/innovations/<str:feature_name>/', views.api_feature_interaction, name='api_feature_interaction'),
    path('api/unique-features/<str:feature_name>/', views.api_feature_interaction),

    # Ultra-Unique Placement Innovation Suite (7 Brand New Features)
    path('skill-barter/', views.skill_barter_view, name='skill_barter'),
    path('hr-live-stream/', views.hr_live_stream_view, name='hr_live_stream'),
    path('job-attrition/', views.job_attrition_predictor_view, name='job_attrition'),
    path('tpo-transparency/', views.tpo_transparency_view, name='tpo_transparency'),
    path('placement-time-machine/', views.placement_time_machine_view, name='placement_time_machine'),
    path('parents-whatsapp-report/', views.parents_whatsapp_report_view, name='parents_whatsapp_report'),
    path('interview-roaster/', views.ai_interview_roaster_view, name='interview_roaster'),
]

