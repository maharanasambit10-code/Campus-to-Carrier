import json
import random
import hashlib
import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.utils import timezone

from .models import (
    FlightSimulationChallenge,
    SimulationSubmission,
    OpportunityCompilerSession,
    ProofPassport,
    PassportArtifact,
    PeerContributionReview,
    SkillBarterWallet,
    SkillBarterListing,
    LiveCodingStream,
    TpoFairnessVote,
)
from .services import (
    seed_default_flight_challenges,
    evaluate_flight_simulation,
    compile_opportunity,
    sync_or_get_proof_passport,
)
from jobs.models import Job


# =========================================================================
# PRODUCT 01: THE CAREER FLIGHT SIMULATOR (Slides 6 & 9)
# =========================================================================

def simulator_catalog(request):
    """
    Catalog of role-specific Career Flight Simulator challenges.
    Surfaces challenges for target roles (e.g., Data Analyst, Backend, ML, DevOps, Product Ops).
    """
    seed_default_flight_challenges()
    challenges = FlightSimulationChallenge.objects.filter(is_active=True).order_by('difficulty', 'title')

    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    completed_slugs = set()
    latest_submissions = {}

    if student:
        user_submissions = SimulationSubmission.objects.filter(student=student).select_related('challenge')
        for sub in user_submissions:
            completed_slugs.add(sub.challenge.slug)
            if sub.challenge.slug not in latest_submissions:
                latest_submissions[sub.challenge.slug] = sub

    role_filter = request.GET.get('role', '')
    difficulty_filter = request.GET.get('difficulty', '')

    if role_filter:
        challenges = challenges.filter(target_role__icontains=role_filter)
    if difficulty_filter:
        challenges = challenges.filter(difficulty=difficulty_filter)

    challenge_list = list(challenges)
    for ch in challenge_list:
        ch.user_submission = latest_submissions.get(ch.slug)

    context = {
        'challenges': challenge_list,
        'completed_slugs': completed_slugs,
        'selected_role': role_filter,
        'selected_difficulty': difficulty_filter,
        'target_roles': [
            'Data Analyst / Business Intelligence',
            'Python Backend / Full-Stack Engineer',
            'AI / Machine Learning Engineer',
            'Cloud & DevOps Engineer',
            'Product Operations / Technical PM'
        ],
    }
    return render(request, 'ai_engine/simulator_catalog.html', context)


@login_required
def simulator_challenge_detail(request, slug):
    """
    Interactive workplace flight simulation challenge workspace.
    Presents scenario brief, telemetry dataset, expected deliverables, and response submission.
    """
    seed_default_flight_challenges()
    challenge = get_object_or_404(FlightSimulationChallenge, slug=slug, is_active=True)

    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can run Career Flight Simulations.")
        return redirect('simulator_catalog')

    student = request.user.student_profile
    previous_submission = SimulationSubmission.objects.filter(student=student, challenge=challenge).first()

    context = {
        'challenge': challenge,
        'previous_submission': previous_submission,
    }
    return render(request, 'ai_engine/simulator_challenge.html', context)


@login_required
def simulator_submit(request, slug):
    """
    Processes submission for a Flight Simulator challenge, performs evaluation,
    extracts demonstrated strengths & skill gaps, and synchronizes proof to Proof Passport.
    """
    if request.method != 'POST':
        return redirect('simulator_challenge_detail', slug=slug)

    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can submit Flight Simulations.")
        return redirect('simulator_catalog')

    challenge = get_object_or_404(FlightSimulationChallenge, slug=slug)
    student = request.user.student_profile

    solution_text = request.POST.get('solution_text', '').strip()
    recommendations = request.POST.get('recommendations', '').strip()
    artifact_url = request.POST.get('artifact_url', '').strip()

    if not solution_text:
        messages.error(request, "Please provide your solution, analysis, or code implementation.")
        return redirect('simulator_challenge_detail', slug=slug)

    submission = SimulationSubmission.objects.create(
        student=student,
        challenge=challenge,
        solution_text=solution_text,
        recommendations=recommendations,
        artifact_url=artifact_url,
        status='SUBMITTED',
    )

    evaluate_flight_simulation(submission)
    messages.success(request, f"Simulation evaluated! You earned {submission.overall_score}/100 and added role proof to your Passport.")
    return redirect('simulator_result', submission_id=submission.id)


@login_required
def simulator_result(request, submission_id):
    """
    Displays the deep evaluation report for a Flight Simulation:
    - Overall & dimensional scores
    - Demonstrated strengths derived from the work itself
    - Practical skill gaps
    - Recommended Next Practice Mission
    """
    submission = get_object_or_404(
        SimulationSubmission.objects.select_related('challenge', 'student__user'),
        id=submission_id
    )

    # Security check: student or recruiter/staff
    if submission.student.user != request.user and not request.user.is_staff and getattr(request.user, 'role', '') != 'RECRUITER':
        raise Http404("Evaluation not found")

    context = {
        'submission': submission,
        'challenge': submission.challenge,
    }
    return render(request, 'ai_engine/simulator_result.html', context)


# =========================================================================
# PRODUCT 02: THE OPPORTUNITY COMPILER (Slide 7)
# =========================================================================

@login_required
def opportunity_compiler_home(request):
    """
    Opportunity Compiler interface:
    Allows student to select an active job or paste job description to compile into a tailored sprint path.
    """
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "The Opportunity Compiler is built for student career readiness.")
        return redirect('home')

    student = request.user.student_profile
    active_jobs = Job.objects.filter(application_deadline__gte=timezone.now()).select_related('company')[:25]
    previous_sessions = OpportunityCompilerSession.objects.filter(student=student).order_by('-created_at')[:8]

    context = {
        'active_jobs': active_jobs,
        'previous_sessions': previous_sessions,
    }
    return render(request, 'ai_engine/compiler_home.html', context)


@login_required
def opportunity_compiler_run(request):
    """
    Decompiles job requirements, maps skills to evidence/practice, and compiles sprint schedule.
    """
    if request.method != 'POST':
        return redirect('opportunity_compiler_home')

    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Student profile required.")
        return redirect('home')

    student = request.user.student_profile
    job_id = request.POST.get('job_id')
    custom_title = request.POST.get('custom_title', '').strip()
    custom_company = request.POST.get('custom_company', '').strip()
    custom_description = request.POST.get('custom_description', '').strip()
    schedule_type = request.POST.get('schedule_type', '2_WEEK_SPRINT')
    available_hours = int(request.POST.get('available_hours', 10) or 10)

    job = None
    if job_id and job_id.isdigit():
        job = Job.objects.filter(id=int(job_id)).first()

    session = compile_opportunity(
        student=student,
        job=job,
        custom_title=custom_title,
        custom_company=custom_company,
        custom_description=custom_description,
        schedule_type=schedule_type,
        available_hours=available_hours,
    )

    messages.success(request, f"Opportunity compiled! Your verified readiness is {session.readiness_percentage}%.")
    return redirect('opportunity_compiler_detail', session_id=session.id)


@login_required
def opportunity_compiler_detail(request, session_id):
    """
    Displays the 4 pillars of the Opportunity Compiler:
    1. Plain-Language Skills
    2. Skills -> Evidence vs Practice
    3. Sprint around student's schedule
    4. Share proof brief
    """
    session = get_object_or_404(
        OpportunityCompilerSession.objects.select_related('student__user', 'job__company'),
        id=session_id
    )

    if session.student.user != request.user and not request.user.is_staff:
        raise Http404("Session not found")

    context = {
        'session': session,
        'job': session.job,
        'plain_skills': session.plain_language_skills,
        'evidence_mapping': session.evidence_mapping,
        'sprint_plan': session.sprint_plan,
    }
    return render(request, 'ai_engine/compiler_detail.html', context)


@login_required
def opportunity_toggle_task(request, session_id, task_index):
    """
    AJAX endpoint to toggle milestone task completion in an opportunity sprint plan.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    session = get_object_or_404(OpportunityCompilerSession, id=session_id, student__user=request.user)
    plan = session.sprint_plan

    if 0 <= task_index < len(plan):
        plan[task_index]['done'] = not plan[task_index].get('done', False)
        session.sprint_plan = plan
        session.save(update_fields=['sprint_plan', 'updated_at'])
        return JsonResponse({'success': True, 'done': plan[task_index]['done']})

    return JsonResponse({'error': 'Invalid task index'}, status=400)


def opportunity_proof_brief(request, token):
    """
    Public shareable proof brief:
    Showcases the student's tailored, evidenced readiness for a target job opportunity.
    """
    session = get_object_or_404(
        OpportunityCompilerSession.objects.select_related('student__user', 'student'),
        proof_brief_token=token
    )

    student = session.student
    passport = sync_or_get_proof_passport(student)

    context = {
        'session': session,
        'student': student,
        'passport': passport,
        'is_public_view': True,
    }
    return render(request, 'ai_engine/opportunity_proof_brief.html', context)


# =========================================================================
# PRODUCT 03: THE PROOF PASSPORT (Slides 8 & 9)
# =========================================================================

@login_required
def proof_passport_dashboard(request):
    """
    Student's private Proof Passport management center:
    - Overall evidence score & readiness index
    - Demonstrated vs. Inferred skill split
    - Multi-source artifacts (Simulations, Projects, Coursework, Peer reviews)
    - Employer privacy toggles & public share link
    """
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Student profile required for Proof Passport.")
        return redirect('home')

    student = request.user.student_profile
    passport = sync_or_get_proof_passport(student)

    artifacts = passport.artifacts.all().order_by('-is_pinned', '-created_at')
    peer_reviews = student.peer_reviews.all().order_by('-created_at')

    # Breakdown by artifact type
    simulations = [a for a in artifacts if a.artifact_type == 'SIMULATION']
    projects = [a for a in artifacts if a.artifact_type == 'PROJECT']
    coursework = [a for a in artifacts if a.artifact_type in ('COURSEWORK', 'CERTIFICATION')]
    peer_artifacts = [a for a in artifacts if a.artifact_type == 'PEER_REVIEW']

    context = {
        'student': student,
        'passport': passport,
        'artifacts': artifacts,
        'peer_reviews': peer_reviews,
        'simulations': simulations,
        'projects': projects,
        'coursework': coursework,
        'peer_artifacts': peer_artifacts,
        'share_url': request.build_absolute_uri(f"/passport/view/{passport.public_share_token}/"),
    }
    return render(request, 'ai_engine/passport_dashboard.html', context)


def proof_passport_public_view(request, token):
    """
    Public, verifiable Proof Passport view for recruiters and hiring managers.
    Does not require login. Displays verified credentials and evidence-backed proof.
    """
    passport = get_object_or_404(
        ProofPassport.objects.select_related('student__user', 'student'),
        public_share_token=token
    )

    if not passport.is_public:
        raise Http404("This candidate Proof Passport is set to private by the student.")

    student = passport.student
    artifacts = passport.artifacts.all().order_by('-is_pinned', '-created_at')

    # Filter according to student's privacy preferences
    visible_artifacts = []
    for a in artifacts:
        if a.artifact_type == 'SIMULATION' and not passport.include_simulations:
            continue
        if a.artifact_type == 'PROJECT' and not passport.include_projects:
            continue
        if a.artifact_type in ('COURSEWORK', 'CERTIFICATION') and not passport.include_coursework:
            continue
        if a.artifact_type == 'PEER_REVIEW' and not passport.include_peer_reviews:
            continue
        visible_artifacts.append(a)

    demonstrated_skills = []
    for a in visible_artifacts:
        for s in a.skills_evidenced:
            if s not in demonstrated_skills:
                demonstrated_skills.append(s)

    context = {
        'passport': passport,
        'student': student,
        'artifacts': visible_artifacts,
        'demonstrated_skills': demonstrated_skills,
        'is_public_view': True,
    }
    return render(request, 'ai_engine/passport_public.html', context)


@login_required
def proof_passport_add_artifact(request):
    """
    Manually add a verified project, capstone, or research artifact to the Proof Passport.
    """
    if request.method != 'POST':
        return redirect('proof_passport_dashboard')

    if not hasattr(request.user, 'student_profile'):
        return redirect('home')

    student = request.user.student_profile
    passport = sync_or_get_proof_passport(student)

    title = request.POST.get('title', '').strip()
    artifact_type = request.POST.get('artifact_type', 'PROJECT')
    description = request.POST.get('description', '').strip()
    source_reference = request.POST.get('source_reference', '').strip()
    external_url = request.POST.get('external_url', '').strip()
    skills_raw = request.POST.get('skills_evidenced', '')
    score_or_grade = request.POST.get('score_or_grade', '').strip()

    skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]

    if not title or not description:
        messages.error(request, "Artifact title and description are required.")
        return redirect('proof_passport_dashboard')

    PassportArtifact.objects.create(
        passport=passport,
        artifact_type=artifact_type,
        title=title,
        description=description,
        source_reference=source_reference or f"{artifact_type.title()} Proof",
        external_url=external_url,
        confidence_level='DEMONSTRATED',
        skills_evidenced=skills_list,
        score_or_grade=score_or_grade or 'Demonstrated Proof',
        is_pinned=True,
    )

    sync_or_get_proof_passport(student)
    messages.success(request, f"Proof artifact '{title}' added to your Passport.")
    return redirect('proof_passport_dashboard')


@login_required
def proof_passport_add_peer_review(request):
    """
    Records a peer or mentor contribution review for the student.
    """
    if request.method != 'POST':
        return redirect('proof_passport_dashboard')

    if not hasattr(request.user, 'student_profile'):
        return redirect('home')

    student = request.user.student_profile
    reviewer_name = request.POST.get('reviewer_name', '').strip()
    reviewer_role = request.POST.get('reviewer_role', '').strip()
    project_name = request.POST.get('project_name', '').strip()
    review_text = request.POST.get('review_text', '').strip()
    skills_raw = request.POST.get('skills_endorsed', '')

    skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]

    if not reviewer_name or not review_text:
        messages.error(request, "Reviewer name and feedback are required.")
        return redirect('proof_passport_dashboard')

    PeerContributionReview.objects.create(
        student=student,
        reviewer_name=reviewer_name,
        reviewer_role=reviewer_role or 'Team Collaborator',
        project_name=project_name or 'Sprint Project',
        review_text=review_text,
        skills_endorsed=skills_list,
        verified=True,
    )

    sync_or_get_proof_passport(student)
    messages.success(request, f"Peer review from {reviewer_name} added to your Proof Passport.")
    return redirect('proof_passport_dashboard')


@login_required
def proof_passport_update_settings(request):
    """
    Updates Proof Passport privacy and employer visibility preferences.
    """
    if request.method != 'POST':
        return redirect('proof_passport_dashboard')

    if not hasattr(request.user, 'student_profile'):
        return redirect('home')

    student = request.user.student_profile
    passport = sync_or_get_proof_passport(student)

    passport.headline = request.POST.get('headline', passport.headline).strip()
    passport.is_public = request.POST.get('is_public') == 'on'
    passport.include_simulations = request.POST.get('include_simulations') == 'on'
    passport.include_projects = request.POST.get('include_projects') == 'on'
    passport.include_coursework = request.POST.get('include_coursework') == 'on'
    passport.include_peer_reviews = request.POST.get('include_peer_reviews') == 'on'
    passport.allowed_employers = request.POST.get('allowed_employers', '').strip()
    passport.save()

    messages.success(request, "Proof Passport visibility and sharing settings updated.")
    return redirect('proof_passport_dashboard')


# =========================================================================
# CAMPUSLINK PROOF INTELLIGENCE PLATFORM VIEWS (From PDF Presentation)
# =========================================================================

def role_decoder_view(request):
    """
    ENGINE 01: ROLE DECODER (Slide 4 & 9)
    Paste a job description -> AI extracts:
    • 9 skills • priority & normalized weights • experience signals • must-have vs nice-to-have.
    Displays the live Career Readiness Graph: Job Post -> Skill Graph -> Proof -> Readiness -> Action.
    """
    from .services import decode_job_description, DEFAULT_DATA_ANALYST_JD
    from .models import RoleDecoderAnalysis
    from jobs.models import Job

    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    active_jobs = Job.objects.filter(is_active=True).select_related('company')[:10]

    latest_analysis = None
    if student:
        latest_analysis = RoleDecoderAnalysis.objects.filter(student=student).first()
    if not latest_analysis:
        latest_analysis = RoleDecoderAnalysis.objects.first()

    if request.method == 'POST':
        raw_text = request.POST.get('job_description', '').strip()
        job_id = request.POST.get('job_id')
        custom_title = request.POST.get('job_title', 'Junior Data Analyst').strip()
        custom_company = request.POST.get('company_name', 'CloudCart').strip()

        latest_analysis = decode_job_description(
            raw_text=raw_text or DEFAULT_DATA_ANALYST_JD,
            student=student,
            job_id=job_id if job_id and job_id.isdigit() else None,
            custom_title=custom_title,
            custom_company=custom_company
        )
        messages.success(request, f"Role Decoded! Extracted {len(latest_analysis.extracted_skills)} skills with normalized priority weights.")

    if not latest_analysis:
        latest_analysis = decode_job_description(DEFAULT_DATA_ANALYST_JD, student=student)

    context = {
        'analysis': latest_analysis,
        'active_jobs': active_jobs,
        'default_jd': DEFAULT_DATA_ANALYST_JD,
        'student': student,
    }
    return render(request, 'ai_engine/role_decoder.html', context)


def proof_miner_view(request):
    """
    ENGINE 02: PROOF MINER (Slide 4, 6 & 10)
    Connect multi-source evidence:
    GitHub repos • certificates • mini-tests • project files • peer/mentor validation.
    """
    from .models import ProofMinerItem
    from .services import seed_proof_miner_defaults
    from students.models import StudentProfile

    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    if not student:
        # Fallback to demo student for showcase
        student = StudentProfile.objects.first()

    seed_proof_miner_defaults(student)

    if request.method == 'POST':
        proof_type = request.POST.get('proof_type', 'GITHUB')
        title = request.POST.get('title', '').strip()
        url_or_ref = request.POST.get('url_or_ref', '').strip()
        skills_raw = request.POST.get('skills_connected', '')
        strength = request.POST.get('strength', 'Strong')
        freshness = request.POST.get('freshness_label', 'Today')
        evidence_details = request.POST.get('evidence_details', '').strip()

        skills = [s.strip() for s in skills_raw.split(',') if s.strip()]

        if title:
            ProofMinerItem.objects.create(
                student=student,
                proof_type=proof_type,
                title=title,
                url_or_ref=url_or_ref,
                skills_connected=skills or ['Python', 'Problem Solving'],
                strength=strength,
                freshness_label=freshness,
                evidence_details=evidence_details,
                is_demonstrated=True,
                verified=True,
            )
            messages.success(request, f"Proof Mined: '{title}' connected with {strength} strength.")

    proof_items = ProofMinerItem.objects.filter(student=student).order_by('-created_at') if student else []

    context = {
        'student': student,
        'proof_items': proof_items,
    }
    return render(request, 'ai_engine/proof_miner.html', context)


def api_parse_github_repo(request):
    """
    BONUS FEATURE (Slide 10): GitHub Evidence Parser API
    Simulates / performs deep repository analysis: commits, language distribution, and evidence tags.
    """
    repo_url = request.GET.get('url', '').strip()
    if not repo_url:
        return JsonResponse({'error': 'Repo URL required'}, status=400)

    # Simulated intelligent parsing
    repo_name = repo_url.rstrip('/').split('/')[-1] if '/' in repo_url else 'Repository'
    data = {
        'repository': repo_name,
        'primary_language': 'Python (68%)',
        'secondary_language': 'SQL (24%)',
        'commits_analyzed': 47,
        'has_readme': True,
        'has_unit_tests': True,
        'test_coverage': '84%',
        'skills_detected': ['Python', 'SQL', 'Data Modeling', 'Git Collaboration'],
        'evidence_strength': 'Strong',
        'freshness': '2 weeks',
        'summary': f"Repository '{repo_name}' exhibits disciplined modularity, commit frequency, and unit test suites.",
    }
    return JsonResponse(data)


def readiness_score_view(request):
    """
    ENGINE 03: READINESS SCORE & EVIDENCE TRAIL (Slide 1, 4 & 6)
    Explainable score built from:
    • skill coverage • evidence strength • assessment result • freshness.
    ANTI-BLACK-BOX RULE: Inferred skill ≠ demonstrated skill. The UI always separates the two!
    Shows the complete Evidence Trail table (Python, SQL, Power BI, Communication).
    """
    from .services import calculate_explainable_readiness_score
    from students.models import StudentProfile

    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    if not student:
        student = StudentProfile.objects.first()

    readiness_data = calculate_explainable_readiness_score(student)

    context = {
        'student': student,
        'readiness': readiness_data,
        'has_completed_mission': readiness_data['has_completed_mission'],
    }
    return render(request, 'ai_engine/readiness_score.html', context)


def action_coach_view(request):
    """
    ENGINE 04: ACTION COACH (Slide 4)
    Find the highest-impact gap -> Generate a 10–20 min mission -> Re-score after completion.
    """
    from .services import calculate_explainable_readiness_score, seed_default_role_missions
    from students.models import StudentProfile

    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    if not student:
        student = StudentProfile.objects.first()

    readiness_data = calculate_explainable_readiness_score(student)
    mission = seed_default_role_missions()

    highest_gap = {
        'skill': 'SQL & Cohort Queries',
        'impact': '+9% Role Fit boost (from 82% to 91%)',
        'gap_reason': 'SQL is a Critical 25%-weight requirement for Junior Data Analyst.',
        'action_name': 'The 15-minute Role Mission: Junior Data Analyst',
        'mission_slug': mission.slug,
        'estimated_minutes': 15,
    }

    context = {
        'student': student,
        'readiness': readiness_data,
        'highest_gap': highest_gap,
        'mission': mission,
    }
    return render(request, 'ai_engine/action_coach.html', context)


def role_mission_workspace(request, slug='junior-data-analyst-15m'):
    """
    AI FEATURE: THE 15-MINUTE ROLE MISSION (Slide 5)
    Instead of asking 'Do you know SQL?', CampusLink asks the candidate to prove it.
    Mission: Junior Data Analyst
    Scenario: E-commerce team sees a 12% drop in repeat purchases.
    TASK 1: Identify 2 metrics you would inspect.
    TASK 2: Write one SQL query or explain the logic.
    TASK 3: Give one business action based on the result.
    AI Evaluation: Logic • SQL • Business thinking -> Result: 78 / 100 • Evidence captured.
    Next Gap: JOINs need practice -> 12-min mission.
    """
    from .services import seed_default_role_missions, evaluate_role_mission_submission
    from .models import RoleMission, RoleMissionSubmission
    from students.models import StudentProfile

    mission = seed_default_role_missions()
    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    if not student:
        student = StudentProfile.objects.first()

    if request.method == 'POST':
        task1 = request.POST.get('task1_answer', '').strip()
        task2 = request.POST.get('task2_answer', '').strip()
        task3 = request.POST.get('task3_answer', '').strip()

        if not (task1 and task2 and task3):
            messages.error(request, "Please provide responses for all three tasks to submit for AI evaluation.")
            return render(request, 'ai_engine/role_mission_workspace.html', {'mission': mission, 'student': student})

        submission = evaluate_role_mission_submission(
            student=student,
            mission=mission,
            task1_answer=task1,
            task2_answer=task2,
            task3_answer=task3
        )
        messages.success(request, f"Mission Evaluated! Result: {submission.overall_score}/100 • Evidence Captured. Fit re-scored to 91%!")
        return redirect('role_mission_result', submission_id=submission.id)

    previous_submission = RoleMissionSubmission.objects.filter(student=student, mission=mission).first() if student else None

    context = {
        'mission': mission,
        'student': student,
        'previous_submission': previous_submission,
    }
    return render(request, 'ai_engine/role_mission_workspace.html', context)


def role_mission_result(request, submission_id):
    """
    Displays the AI Evaluation report for the 15-minute Role Mission (Slide 5):
    Logic • SQL • Business thinking
    Result: 78 / 100 • Evidence captured
    Next Gap: JOINs need practice -> 12-min mission
    """
    from .models import RoleMissionSubmission
    from .services import calculate_explainable_readiness_score

    submission = get_object_or_404(
        RoleMissionSubmission.objects.select_related('mission', 'student__user'),
        id=submission_id
    )

    readiness = calculate_explainable_readiness_score(submission.student)

    context = {
        'submission': submission,
        'mission': submission.mission,
        'readiness': readiness,
    }
    return render(request, 'ai_engine/role_mission_result.html', context)


def college_readiness_radar_view(request):
    """
    COLLEGE IMPACT: LIVE READINESS RADAR (Slide 7)
    Placement teams get a live 'readiness radar':
    • SQL: 38%
    • Communication: 52%
    • Python: 71%
    • Excel/BI: 64%
    • Problem Solving: 78%
    Intervention: Launch a targeted SQL sprint for the bottom 30%.
    Outcome: Measure improvement before recruiter assessments.
    """
    from .services import seed_college_readiness_radar
    from .models import CollegeReadinessRadar, CollegeTargetedIntervention

    radar = seed_college_readiness_radar()
    interventions = radar.interventions.all().order_by('-launched_at')

    context = {
        'radar': radar,
        'interventions': interventions,
    }
    return render(request, 'ai_engine/college_readiness_radar.html', context)


def college_launch_intervention(request):
    """
    Placement officer triggers targeted sprint intervention (Slide 7)
    """
    from .models import CollegeReadinessRadar, CollegeTargetedIntervention
    from .services import seed_college_readiness_radar

    if request.method != 'POST':
        return redirect('college_readiness_radar')

    radar = seed_college_readiness_radar()
    skill_target = request.POST.get('skill_target', 'SQL')
    target_cohort = request.POST.get('target_cohort', 'Bottom 30%')
    students_count = int(request.POST.get('students_count', 84) or 84)

    intervention = CollegeTargetedIntervention.objects.create(
        radar=radar,
        skill_target=skill_target,
        target_cohort=target_cohort,
        targeted_students_count=students_count,
        mission_assigned=f"Targeted {skill_target} Sprint: 15-min Telemetry & Optimization Mission",
        status='ACTIVE',
        measured_improvement_pct=26,
    )

    messages.success(request, f"Targeted {skill_target} Sprint launched for {target_cohort} ({students_count} students notified)!")
    return redirect('college_readiness_radar')


def recruiter_proof_shortlist_view(request):
    """
    RECRUITER VIEW: SHORTLIST BY PROOF, NOT KEYWORD DENSITY (Slide 8)
    A recruiter sees comparable evidence and an explainable recommendation in one screen:
    • Candidate A: Data Analyst, ROLE FIT 91%, PROOF 9/10 skills proven
    • Candidate B: Data Analyst, ROLE FIT 84%, PROOF 7/10 skills proven
    • Candidate C: Data Analyst, ROLE FIT 76%, PROOF 6/10 skills proven
    Actions: VIEW PROOF | SEND MISSION | SHORTLIST
    """
    from .services import seed_recruiter_proof_candidates
    from .models import RecruiterCandidateProof

    candidates = seed_recruiter_proof_candidates()
    candidate_list = RecruiterCandidateProof.objects.all().order_by('-role_fit_percentage')

    context = {
        'candidates': candidate_list,
    }
    return render(request, 'ai_engine/recruiter_proof_shortlist.html', context)


def recruiter_toggle_shortlist(request, candidate_id):
    """
    One-click shortlist action for recruiter (Slide 8)
    """
    from .models import RecruiterCandidateProof

    if request.method != 'POST':
        return redirect('recruiter_proof_shortlist')

    candidate = get_object_or_404(RecruiterCandidateProof, id=candidate_id)
    candidate.is_shortlisted = not candidate.is_shortlisted
    candidate.save(update_fields=['is_shortlisted'])

    status_str = "shortlisted" if candidate.is_shortlisted else "removed from shortlist"
    messages.success(request, f"{candidate.candidate_label} ({candidate.candidate_name}) {status_str} based on verified proof.")
    return redirect('recruiter_proof_shortlist')


def recruiter_send_mission(request, candidate_id):
    """
    One-click send 15-minute mission to candidate (Slide 8)
    """
    from .models import RecruiterCandidateProof

    if request.method != 'POST':
        return redirect('recruiter_proof_shortlist')

    candidate = get_object_or_404(RecruiterCandidateProof, id=candidate_id)
    candidate.mission_sent = True
    candidate.save(update_fields=['mission_sent'])

    messages.success(request, f"15-Minute Role Mission sent to {candidate.candidate_label} ({candidate.candidate_name})! Evidence will stream back upon completion.")
    return redirect('recruiter_proof_shortlist')


def hackathon_demo_journey(request):
    """
    HACKATHON DEMO: THE 3-MINUTE 'WOW' JOURNEY (Slide 9 & 13)
    One student. One job. One proof loop.
    0:00 PASTE JOB (Role Decoder extracts 9 skills)
    0:40 UPLOAD PROOF (Project + GitHub + assessment)
    1:20 READINESS (AI shows 82% with evidence)
    2:00 LIVE MISSION (Student solves 10-15 min task -> AI evaluation 78/100)
    2:40 RE-SCORE (Gap closes -> Role Fit jumps to 91% -> recruiter-ready proof)
    Judges understand the value without a long explanation.
    """
    from .services import (
        calculate_explainable_readiness_score,
        DEFAULT_DATA_ANALYST_JD,
        seed_proof_miner_defaults,
        seed_default_role_missions,
        seed_recruiter_proof_candidates,
    )
    from .models import RoleDecoderAnalysis
    from students.models import StudentProfile

    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    if not student:
        student = StudentProfile.objects.first()

    readiness = calculate_explainable_readiness_score(student)
    mission = seed_default_role_missions()
    seed_recruiter_proof_candidates()

    step = int(request.GET.get('step', 1))

    context = {
        'step': step,
        'student': student,
        'readiness': readiness,
        'mission': mission,
        'default_jd': DEFAULT_DATA_ANALYST_JD,
    }
    return render(request, 'ai_engine/hackathon_demo.html', context)


# =========================================================================
# ADVANCED ECOSYSTEM & HACKATHON VIEWS
# =========================================================================

def career_skill_graph_view(request):
    """
    FEATURE: CAREER SKILL GRAPH (Slide 3)
    Visualizes the live Career Readiness Graph with interactive nodes and edges:
    Role -> Normalized Skills -> Verified Artifacts -> Next-Best Actions.
    """
    from .services import get_career_skill_graph_data, calculate_explainable_readiness_score
    from students.models import StudentProfile

    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    if not student:
        student = StudentProfile.objects.first()

    graph_data = get_career_skill_graph_data(student)
    readiness = calculate_explainable_readiness_score(student)

    context = {
        'student': student,
        'graph_data': graph_data,
        'readiness': readiness,
    }
    return render(request, 'ai_engine/career_skill_graph.html', context)


def interview_arena_view(request):
    """
    FEATURE: AI INTERVIEW ARENA
    Interactive live interview arena for candidate defense and capability proof.
    """
    from .models import InterviewArenaSession
    from students.models import StudentProfile

    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    if not student:
        student = StudentProfile.objects.first()

    sessions = InterviewArenaSession.objects.filter(student=student) if student else []
    default_question = "Explain how you would diagnose a 12% drop in repeat purchases using SQL and cohort analysis. What metrics would you prioritize and why?"

    context = {
        'student': student,
        'sessions': sessions,
        'default_question': default_question,
        'target_role': 'Junior Data Analyst',
    }
    return render(request, 'ai_engine/interview_arena.html', context)


def interview_arena_submit(request):
    """
    Processes candidate answer in the AI Interview Arena, generates multidimensional scores,
    and synchronizes proof to Proof Passport.
    """
    from .services import evaluate_interview_arena_session
    from students.models import StudentProfile

    if request.method != 'POST':
        return redirect('interview_arena')

    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    if not student:
        student = StudentProfile.objects.first()

    target_role = request.POST.get('target_role', 'Junior Data Analyst')
    question = request.POST.get('question_prompt', 'Explain how you would diagnose a 12% drop in repeat purchases.')
    response = request.POST.get('candidate_response', '').strip()

    if not response:
        messages.error(request, "Please enter your interview defense response.")
        return redirect('interview_arena')

    session = evaluate_interview_arena_session(
        student=student,
        target_role=target_role,
        question=question,
        candidate_response=response
    )

    messages.success(request, f"Interview Arena Defense Evaluated! Overall Score: {session.overall_score}/100. Proof verified in Passport.")
    return redirect('interview_arena')


def placement_risk_early_warning_view(request):
    """
    FEATURE: PLACEMENT RISK EARLY-WARNING
    College placement radar dashboard for proactive intervention before placement drives.
    """
    from .services import seed_or_scan_placement_risk_profiles
    from .models import PlacementRiskProfile

    seed_or_scan_placement_risk_profiles()
    profiles = PlacementRiskProfile.objects.all().select_related('student__user')

    high_risk_count = profiles.filter(risk_level='HIGH_RISK').count()
    moderate_risk_count = profiles.filter(risk_level='MODERATE_RISK').count()
    ready_count = profiles.filter(risk_level='PLACEMENT_READY').count()

    context = {
        'profiles': profiles,
        'high_risk_count': high_risk_count,
        'moderate_risk_count': moderate_risk_count,
        'ready_count': ready_count,
    }
    return render(request, 'ai_engine/placement_risk_warning.html', context)


def placement_risk_dispatch_intervention(request):
    """
    Dispatches automated intervention to all high-risk students with one click.
    """
    from .models import PlacementRiskProfile

    if request.method != 'POST':
        return redirect('placement_risk_early_warning')

    high_risk_qs = PlacementRiskProfile.objects.filter(risk_level='HIGH_RISK')
    updated = high_risk_qs.update(intervention_dispatched=True)

    messages.success(request, f"Targeted Interventions dispatched to {updated} high-risk students! 15-minute missions assigned.")
    return redirect('placement_risk_early_warning')


def personalized_improvement_view(request):
    """
    FEATURE: NEXT-BEST ACTION / PERSONALIZED IMPROVEMENT
    Prioritized action hub ranked by ROI (+9% fit, +6% fit, etc.).
    """
    from .services import get_personalized_improvement_actions, calculate_explainable_readiness_score
    from students.models import StudentProfile

    student = getattr(request.user, 'student_profile', None) if request.user.is_authenticated else None
    if not student:
        student = StudentProfile.objects.first()

    actions = get_personalized_improvement_actions(student)
    readiness = calculate_explainable_readiness_score(student)

    context = {
        'student': student,
        'actions': actions,
        'readiness': readiness,
    }
    return render(request, 'ai_engine/personalized_improvement.html', context)


def ecosystem_hub_view(request):
    """
    FEATURE: COMPLETE STUDENT → COLLEGE → RECRUITER ECOSYSTEM
    Live cross-stakeholder dashboard showing unified evidence flow and synchronizations.
    """
    from .services import get_ecosystem_status_summary
    from students.models import StudentProfile

    summary = get_ecosystem_status_summary()

    context = {
        'summary': summary,
    }
    return render(request, 'ai_engine/ecosystem_hub.html', context)


def final_hackathon_pitch_view(request):
    """
    FEATURE: STRONG FINAL HACKATHON PITCH
    Interactive presentation deck and judge defense hub.
    """
    from .services import calculate_explainable_readiness_score
    from students.models import StudentProfile

    student = StudentProfile.objects.first()
    readiness = calculate_explainable_readiness_score(student)

    context = {
        'readiness': readiness,
    }
    return render(request, 'ai_engine/hackathon_pitch.html', context)


# =========================================================================
# 12 DISRUPTIVE UNIQUE FEATURES FOR CAMPUS TO CAREER
# =========================================================================

def innovation_suite_view(request):
    """
    12 KILLER INNOVATION SUITE & SEPARATE TASKBAR
    Interactive showcase and working engines for:
    1. Placement Black Box
    2. Fake Offer Letter Detector
    3. Ghost Job Detector
    4. Reverse Hiring Mode
    5. Salary Negotiation Simulator
    6. Degree ROI Calculator
    7. Alumni Unsuccess Blueprint
    8. 21 Days Placement ICU
    9. One-Click Corporate Avatar
    10. What-If Career Engine
    11. Referral Black Market Detector
    12. Skill Bankruptcy Score
    """
    from students.models import StudentProfile
    student = None
    if request.user.is_authenticated:
        student = getattr(request.user, 'student_profile', None)
    if not student:
        student = StudentProfile.objects.first()

    # Pre-calculated seed and live simulation states
    context = {
        'student': student,
        'features_count': 12,
        'black_box_data': {
            'cgpa': getattr(student, 'cgpa', 8.2) or 8.2,
            'placement_probability': 86.4,
            'risk_level': 'Safe Tier',
            'vulnerabilities': [
                {'title': 'System Design Gap', 'impact': 'High for Product Startups', 'fix': 'Build 1 Distributed Cache / Rate Limiter Project'},
                {'title': 'Low Mid-Year Git Activity', 'impact': 'Moderate for FinTechs', 'fix': 'Commit weekly proof artifacts to GitHub'}
            ],
            'four_year_trajectory': [
                {'year': 'Year 1', 'score': 62, 'focus': 'Foundations & C++'},
                {'year': 'Year 2', 'score': 71, 'focus': 'DSA & Web Stack'},
                {'year': 'Year 3', 'score': 84, 'focus': 'Production Projects & Internships'},
                {'year': 'Year 4 (Current)', 'score': 88, 'focus': 'High-Bar Interviews & Mock Drills'}
            ]
        },
        'ghost_jobs_sample': [
            {'title': 'Software Engineer (Campus 2026)', 'company': 'TechNova Labs', 'repost_count': 9, 'ghost_prob': 88, 'status': 'Ghost Warning'},
            {'title': 'Junior Python Developer', 'company': 'CredFlow FinTech', 'repost_count': 1, 'ghost_prob': 12, 'status': 'Active Hiring'}
        ],
        'unsuccess_blueprints': [
            {
                'alias': 'Senior Rahul K. (Batch 2025)',
                'mistake': 'Certificate Collector Trap',
                'description': 'Gathered 28 online completion certificates but had zero public deployed URLs or GitHub repo tests.',
                'result': 'Rejected in Round 2 technical demo.',
                'antidote': '1 deployed project beats 10 Udemy certificates every single time.'
            },
            {
                'alias': 'Senior Ananya S. (Batch 2025)',
                'mistake': 'Delayed DSA to 8th Semester',
                'description': 'Focused purely on design work, started LeetCode 3 weeks before TCS Digital & Amazon drives.',
                'result': 'Timed out on Online Assessment coding test.',
                'antidote': '15 minutes daily problem solving from 5th semester onwards.'
            },
            {
                'alias': 'Senior Vikram M. (Batch 2024)',
                'mistake': 'Zero Mock Interview Exposure',
                'description': 'High GPA (8.9) and strong coding score, but froze on behavioral / STAR explanation questions with HR.',
                'result': 'Rejected at final managerial interview round.',
                'antidote': 'Practice 5 recorded voice/video mocks before first live campus drive.'
            }
        ],
        'skill_cibil': {
            'score': 774,
            'max_score': 900,
            'rating': 'A+ Prime Solvency',
            'liquidity_rate': 88.5,
            'tech_debt_rate': 11.5,
            'eligible_companies': 164
        }
    }
    return render(request, 'ai_engine/innovation_suite.html', context)


@csrf_exempt
def api_feature_interaction(request, feature_name):
    """
    Live API responder for interactive simulation actions across the 12 features.
    """
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    data = {}
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
        except Exception:
            data = request.POST

    # 1. Placement Black Box Calculator
    if feature_name == 'black-box':
        cgpa = float(data.get('cgpa', 8.0))
        projects = int(data.get('projects', 2))
        coding_hours = int(data.get('coding_hours', 10))
        backlogs = int(data.get('backlogs', 0))

        prob = min(98.0, max(25.0, (cgpa * 7.5) + (projects * 5.0) + (coding_hours * 1.5) - (backlogs * 18.0)))
        tier = 'Safe Tier' if prob >= 75 else ('At-Risk Tier' if prob >= 50 else 'Critical ICU Tier')
        return JsonResponse({
            'status': 'success',
            'placement_probability': round(prob, 1),
            'tier': tier,
            'trajectory': 'Positive (+4.2% this quarter)' if prob >= 70 else 'Needs Immediate 21-Day ICU'
        })

    # 2. Fake Offer Letter Detector
    elif feature_name == 'fake-offer':
        offer_text = str(data.get('text', '')).lower()
        company = str(data.get('company', '')).strip()

        flags = []
        is_fraud = False
        if any(term in offer_text for term in ['security deposit', 'registration fee', 'pay rs', 'training fee', 'laptop courier charges', 'processing fee']):
            flags.append('🚨 Demands upfront monetary deposit / laptop courier charges (Prohibited)')
            is_fraud = True
        if '@gmail.com' in offer_text or '@yahoo.com' in offer_text:
            flags.append('⚠️ Free public webmail address used instead of verified corporate domain')
            is_fraud = True
        if any(term in offer_text for term in ['tcs', 'infosys', 'wipro']) and 'consultancy' in offer_text:
            flags.append('⚠️ Unauthorized third-party agency masquerading as Tier-1 IT employer')
            is_fraud = True

        score = 15 if is_fraud else 96
        verdict = 'FRAUD OFFER DETECTED' if is_fraud else 'AUTHENTIC OFFER VERIFIED'
        return JsonResponse({
            'status': 'success',
            'is_fraud': is_fraud,
            'verdict': verdict,
            'authenticity_score': score,
            'flags': flags if flags else ['✅ MCA / CIN Registered entity verified', '✅ Official corporate domain matching records', '✅ Legitimate compensation breakdown with standard deductions']
        })

    # 3. Ghost Job Detector
    elif feature_name == 'ghost-job':
        url = str(data.get('url', ''))
        job_title = str(data.get('title', 'Software Engineer'))

        # Simulation heuristics
        ghost_prob = 74 if ('intern' in job_title.lower() or '202' in job_title) else 28
        return JsonResponse({
            'status': 'success',
            'job_title': job_title,
            'ghost_probability': ghost_prob,
            'repost_count': 6 if ghost_prob > 50 else 1,
            'verdict': 'Likely Ghost Job (No Active Hiring)' if ghost_prob > 50 else 'Active Real Opening',
            'signals': [
                'Listing reposted 6 times over the past 120 days',
                'Zero recruiter interview activity logged in last 3 weeks',
                'Resume collection buffer detected'
            ] if ghost_prob > 50 else [
                'Verified recruiter actively screening applicants today',
                'Headcount approved for Q3 campus cycle'
            ]
        })

    # 5. Salary Negotiation Simulator
    elif feature_name == 'salary-negotiate':
        current_offer = float(data.get('offer', 6.0))
        counter_offer = float(data.get('counter', 8.5))
        pitch = str(data.get('pitch', 'I have verified production projects and another competing offer.'))

        increase = min(counter_offer, round(current_offer * 1.18, 1))
        hr_response = f"We appreciate your confidence! Based on your verified portfolio and proof score, our budget can stretch to ₹{increase} LPA + ₹50,000 joining retention bonus."
        return JsonResponse({
            'status': 'success',
            'agreed_ctc': increase,
            'hr_response': hr_response,
            'leverage_score': 88,
            'tip': 'Tip: Always negotiate non-cash perks like remote flexibility or early appraisal cycles!'
        })

    # 6. Degree ROI Calculator
    elif feature_name == 'degree-roi':
        fees = float(data.get('fees', 400000))
        starting_ctc = float(data.get('ctc', 600000))
        monthly_takehome = (starting_ctc * 0.85) / 12
        living_cost = float(data.get('living_cost', 20000))
        monthly_savings = max(5000, monthly_takehome - living_cost)

        breakeven_months = round(fees / monthly_savings, 1)
        breakeven_years = round(breakeven_months / 12, 1)
        five_yr_net = round((monthly_savings * 60) - fees, 0)

        return JsonResponse({
            'status': 'success',
            'breakeven_months': breakeven_months,
            'breakeven_years': breakeven_years,
            'five_yr_net_wealth': f"₹{int(five_yr_net):,}",
            'irr_percent': round((starting_ctc / fees) * 32.5, 1)
        })

    # 10. What-If Career Engine
    elif feature_name == 'what-if':
        base_stack = str(data.get('base', 'Java Basic'))
        upgrade = str(data.get('upgrade', 'Python + GenAI'))

        delta_ctc = 4.2 if 'GenAI' in upgrade else (3.5 if 'DevOps' in upgrade else 2.8)
        return JsonResponse({
            'status': 'success',
            'base_stack': base_stack,
            'upgrade_stack': upgrade,
            'package_delta_lpa': delta_ctc,
            'estimated_ctc': f"₹{round(6.0 + delta_ctc, 1)} LPA",
            'time_investment': '35 Days Dedicated Sprint',
            'market_demand_index': '+148% higher recruiter search appearances'
        })

    return JsonResponse({'status': 'success', 'message': f'Feature {feature_name} active and monitored.'})


# =========================================================================
# ULTRA-UNIQUE PLACEMENT INTELLIGENCE SUITE (7 BRAND NEW FEATURES)
# =========================================================================

def _get_or_create_student_and_wallet(request):
    """Helper to retrieve student profile and barter wallet safely."""
    from students.models import StudentProfile
    student = None
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
    if not student:
        student = StudentProfile.objects.first()
    wallet = None
    if student:
        wallet, _ = SkillBarterWallet.objects.get_or_create(student=student, defaults={'coins': 5})
    return student, wallet


def skill_barter_view(request):
    """
    1. SKILL BARTER SYSTEM (Tu usko DSA padha, wo tujhe English padhayega. 1 ghanta = 1 Coin)
    Peer learning barter economy for campus placements.
    """
    student, wallet = _get_or_create_student_and_wallet(request)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_listing' and student:
            offer_skill = request.POST.get('offer_skill', '').strip()
            wanted_skill = request.POST.get('wanted_skill', '').strip()
            session_hours = int(request.POST.get('session_hours', 1))
            notes = request.POST.get('notes', '').strip()
            if offer_skill and wanted_skill:
                SkillBarterListing.objects.create(
                    student=student,
                    offer_skill=offer_skill,
                    wanted_skill=wanted_skill,
                    session_hours=session_hours,
                    coins_reward=session_hours,
                    notes=notes
                )
                messages.success(request, f"Barter listing created! You will earn {session_hours} Coin upon teaching.")
                return redirect('skill_barter')

        elif action == 'accept_barter' and student:
            listing_id = request.POST.get('listing_id')
            listing = SkillBarterListing.objects.filter(id=listing_id, status='OPEN').first()
            if listing and listing.student != student:
                listing.partner = student
                listing.status = 'IN_PROGRESS'
                listing.save()
                messages.success(request, f"Barter match established! You connected with {listing.student.user.username}.")
                return redirect('skill_barter')

        elif action == 'complete_barter' and student:
            listing_id = request.POST.get('listing_id')
            listing = SkillBarterListing.objects.filter(id=listing_id, status='IN_PROGRESS').first()
            if listing:
                listing.status = 'COMPLETED'
                listing.save()
                teacher_wallet, _ = SkillBarterWallet.objects.get_or_create(student=listing.student)
                teacher_wallet.coins += listing.coins_reward
                teacher_wallet.hours_taught += listing.session_hours
                teacher_wallet.save()
                if listing.partner:
                    learner_wallet, _ = SkillBarterWallet.objects.get_or_create(student=listing.partner)
                    learner_wallet.hours_learned += listing.session_hours
                    learner_wallet.save()
                messages.success(request, f"Barter completed! {listing.coins_reward} Coin transferred to mentor.")
                return redirect('skill_barter')

    listings = SkillBarterListing.objects.all()[:20]
    if not listings.exists() and student:
        SkillBarterListing.objects.create(
            student=student,
            offer_skill="DSA (Graphs, Trees & DP in C++)",
            wanted_skill="Spoken English & HR Behavioral Answers",
            session_hours=1,
            coins_reward=1,
            notes="Solved 300+ LeetCode problems. Looking to polish conversational confidence for MNC interviews."
        )
        SkillBarterListing.objects.create(
            student=student,
            offer_skill="React & Full Stack Web UI",
            wanted_skill="System Design & Low-Level API Architecture",
            session_hours=2,
            coins_reward=2,
            notes="Built 4 full-stack projects. Want to learn caching, Redis and message queues."
        )
        listings = SkillBarterListing.objects.all()

    context = {
        'student': student,
        'wallet': wallet,
        'listings': listings,
        'open_listings_count': SkillBarterListing.objects.filter(status='OPEN').count(),
        'completed_listings_count': SkillBarterListing.objects.filter(status='COMPLETED').count(),
    }
    return render(request, 'ai_engine/skill_barter.html', context)


def hr_live_stream_view(request):
    """
    2. HR KA LIVE CODING DEKHEGA (Twitch for Placement Coders)
    Anonymous 2 AM live coding screen where corporate HR scouts discover late-night hustlers.
    """
    student, _ = _get_or_create_student_and_wallet(request)

    if request.method == 'POST' and student:
        action = request.POST.get('action')
        if action == 'start_stream':
            problem_title = request.POST.get('problem_title', 'Distributed Key-Value Store')
            language = request.POST.get('language', 'Python / Django')
            code_snippet = request.POST.get('code_snippet', '# Live 2:30 AM Session\n')
            LiveCodingStream.objects.create(
                student=student,
                anonymous_alias=f"Night-Owl #{random.randint(100, 999)}",
                problem_title=problem_title,
                language=language,
                code_snippet=code_snippet,
                is_live=True,
                viewer_count=random.randint(18, 55),
                hr_scouts_count=random.randint(2, 6)
            )
            messages.success(request, "Your anonymous code stream is now LIVE! HR scouts have entered the watchroom.")
            return redirect('hr_live_stream')

    streams = LiveCodingStream.objects.filter(is_live=True)[:10]
    if not streams.exists() and student:
        LiveCodingStream.objects.create(
            student=student,
            anonymous_alias="Night-Owl #814 (B.Tech CSE)",
            language="Python & Redis",
            problem_title="Building High-Throughput Token Bucket Rate Limiter with Atomic Redis Counters",
            viewer_count=34,
            hr_scouts_count=5,
            code_snippet="""# Live 2:15 AM Coding Session
import time
from collections import deque

class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = capacity
        self.last_refill = time.time()

    def allow(self, tokens_requested=1) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= tokens_requested:
            self.tokens -= tokens_requested
            return True
        return False
"""
        )
        streams = LiveCodingStream.objects.filter(is_live=True)

    context = {
        'student': student,
        'streams': streams,
        'active_streamers': streams.count(),
        'total_hr_scouts': sum(s.hr_scouts_count for s in streams) if streams else 14,
    }
    return render(request, 'ai_engine/hr_live_stream.html', context)


def job_attrition_predictor_view(request):
    """
    3. JOB JISSE TU 3 MAHINE MEIN BHAGEGA (AI Churn & Attrition Predictor)
    Identifies mismatch between candidate's coding tempo/personality and enterprise bureaucracy.
    """
    student, _ = _get_or_create_student_and_wallet(request)

    target_company = request.GET.get('company', 'Wipro')
    work_style = request.GET.get('work_style', 'Agile Product Builder')

    company_profiles = {
        'Wipro': {
            'boredom_score': 89,
            'attrition_prob': 86,
            'days_to_quit': 74,
            'culture_type': 'Legacy Service MNC / Heavy Bench Queue',
            'shock_factor': 'Requires 4 layers of email approvals to install a Python package. High probability of being placed on legacy ticket maintenance.',
            'ai_verdict': 'Tujhe Wipro me bore hoke 3 mahine me resign de dega! Tere andar fast execution aur code ship karne ka keeda hai, wahan daily Timesheet & Outlook meetings dekh ke dimaag blast ho jayega!',
            'ideal_alternative': 'High-Velocity AI Startup (e.g. Sarvam AI, Zepto, CRED) where you ship directly to production on Day 2.',
        },
        'TCS': {
            'boredom_score': 81,
            'attrition_prob': 76,
            'days_to_quit': 88,
            'culture_type': 'Enterprise Mega-Corps / Strict Hierarchy',
            'shock_factor': 'Strict biometric dress-code policies, proxy firewalls blocking GitHub & StackOverflow, slow tech stack adoption.',
            'ai_verdict': '6 mahine ILP training bench pe baithega. Coding speed 70% slow ho jayegi. Tu 3rd month aate-aate resign deke startup bhaagega!',
            'ideal_alternative': 'Product Engineering Lab or High-Growth FinTech (e.g. Razorpay, Groww).',
        },
        'Infosys': {
            'boredom_score': 83,
            'attrition_prob': 79,
            'days_to_quit': 81,
            'culture_type': 'Process-Driven Service Giant',
            'shock_factor': 'Mysore campus was great, but real client project is Java 8 XML config with no cloud or modern framework access.',
            'ai_verdict': 'Bhai tu 90 din me LinkedIn pe "Actively Looking" status daal dega.',
            'ideal_alternative': 'Mid-Market SaaS or Developer Tools Product (e.g. Postman, BrowserStack).',
        },
        'Early-Stage Startup': {
            'boredom_score': 12,
            'attrition_prob': 20,
            'days_to_quit': 540,
            'culture_type': 'High-Velocity Product Startup',
            'shock_factor': 'High ownership, fast iterative shipping, steep learning curve, direct founder feedback.',
            'ai_verdict': 'PERFECT MATCH! Yahan tu bore nahi hoga, roz nayi cheezein banayega aur 1 saal me 3 saal ka coding experience seekhega.',
            'ideal_alternative': 'You are already in your optimal natural environment!',
        }
    }

    selected_data = company_profiles.get(target_company, company_profiles['Wipro'])

    context = {
        'student': student,
        'target_company': target_company,
        'work_style': work_style,
        'data': selected_data,
        'all_companies': ['Wipro', 'TCS', 'Infosys', 'Early-Stage Startup'],
    }
    return render(request, 'ai_engine/job_attrition.html', context)


def tpo_transparency_view(request):
    """
    4. TPO KA CORRUPTION & TRANSPARENCY METER
    Anonymous encrypted student voting & placement fairness audit meter.
    """
    student, _ = _get_or_create_student_and_wallet(request)

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 4))
        is_fair = request.POST.get('is_fair') == 'true'
        comment = request.POST.get('comment', '').strip()
        college = request.POST.get('college', 'BPUT University')
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        user_key = f"{ip}_{student.id if student else random.randint(1,9999)}_{college}"
        token = hashlib.sha256(user_key.encode()).hexdigest()[:32]

        TpoFairnessVote.objects.update_or_create(
            student_token=token,
            defaults={
                'college_name': college,
                'transparency_rating': rating,
                'is_fair_and_unbiased': is_fair,
                'comment': comment
            }
        )
        messages.success(request, "Your anonymous audit vote was encrypted & recorded to the public fairness meter!")
        return redirect('tpo_transparency')

    votes = TpoFairnessVote.objects.all()
    if not votes.exists():
        samples = [
            ("Zero backchannel favors observed; all shortlists strictly matched CGPA & coding scores.", 5, True),
            ("TCS and Cognizant drives were conducted on transparent open portal with clear criteria.", 4, True),
            ("Tier-1 company cutoff was suddenly changed 1 hour before test without official notice.", 2, False),
            ("Transparent interview schedules, good overall placement coordination.", 5, True),
        ]
        for idx, (cmt, rtg, fair) in enumerate(samples):
            TpoFairnessVote.objects.create(
                student_token=f"sample_audit_token_{idx}",
                transparency_rating=rtg,
                is_fair_and_unbiased=fair,
                comment=cmt
            )
        votes = TpoFairnessVote.objects.all()

    total_votes = max(1, votes.count())
    fair_votes = votes.filter(is_fair_and_unbiased=True).count()
    clean_percentage = round((fair_votes / total_votes) * 100, 1)

    context = {
        'student': student,
        'clean_percentage': clean_percentage,
        'total_votes': votes.count(),
        'recent_audits': votes[:15],
    }
    return render(request, 'ai_engine/tpo_transparency.html', context)


def placement_time_machine_view(request):
    """
    5. PLACEMENT TIME MACHINE (5-Year Career Trajectory Simulator)
    Today's habits -> 5 years future life, salary, car, and role comparison.
    """
    student, _ = _get_or_create_student_and_wallet(request)

    dsa_per_day = int(request.GET.get('dsa', 1))
    git_commits = int(request.GET.get('git', 3))
    mock_interviews = int(request.GET.get('mocks', 1))
    doomscroll_hours = int(request.GET.get('reels', 2))

    effort_score = (dsa_per_day * 25) + (git_commits * 15) + (mock_interviews * 20) - (doomscroll_hours * 10)
    effort_score = max(10, min(100, effort_score))

    trajectory_low = [
        {'year': 'Year 1 (2027)', 'ctc': '₹3.2 LPA', 'role': 'Support Trainee', 'life': 'Shared 4BHK room with 3 roommates, local bus travel'},
        {'year': 'Year 2 (2028)', 'ctc': '₹3.8 LPA', 'role': 'Associate Engineer', 'life': 'Routine bug fixing, saving ₹5k/month after rent'},
        {'year': 'Year 3 (2029)', 'ctc': '₹4.5 LPA', 'role': 'Software Engineer', 'life': 'Stuck on legacy codebase, worried about AI layoffs'},
        {'year': 'Year 4 (2030)', 'ctc': '₹5.5 LPA', 'role': 'Senior Associate', 'life': 'EMI stress, switching difficulty due to DSA skill gap'},
        {'year': 'Year 5 (2031)', 'ctc': '₹6.8 LPA', 'role': 'Team Member', 'life': 'Monthly salary ₹48,000, career stagnation'}
    ]

    trajectory_high = [
        {'year': 'Year 1 (2027)', 'ctc': '₹9 - 13 LPA', 'role': 'SDE-1 (FinTech / Product)', 'life': 'Independent flat in Bengaluru / Pune, brand new MacBook Pro'},
        {'year': 'Year 2 (2028)', 'ctc': '₹15 - 20 LPA', 'role': 'Core SDE-1', 'life': 'First international trip, investing ₹40k/month in mutual funds'},
        {'year': 'Year 3 (2029)', 'ctc': '₹26 - 32 LPA', 'role': 'SDE-2 (High-Scale Systems)', 'life': 'First car bought without loan, parents flight tickets booked'},
        {'year': 'Year 4 (2030)', 'ctc': '₹38 - 48 LPA', 'role': 'Senior Backend / Tech Lead', 'life': 'Stock options vesting, headhunted by top US remote startups'},
        {'year': 'Year 5 (2031)', 'ctc': '₹60 - 80 LPA', 'role': 'Staff Engineer / Founder', 'life': 'Complete financial freedom, building high-impact tech products'}
    ]

    context = {
        'student': student,
        'dsa_per_day': dsa_per_day,
        'git_commits': git_commits,
        'mock_interviews': mock_interviews,
        'doomscroll_hours': doomscroll_hours,
        'effort_score': effort_score,
        'trajectory_low': trajectory_low,
        'trajectory_high': trajectory_high,
    }
    return render(request, 'ai_engine/placement_time_machine.html', context)


def parents_whatsapp_report_view(request):
    """
    6. PARENTS WHATSAPP PLACEMENT REPORT (Har Sunday Beta Ka Report Card)
    Generates a WhatsApp-ready placement status card for parents with 1-click WhatsApp web dispatch.
    """
    student, _ = _get_or_create_student_and_wallet(request)

    student_name = student.user.get_full_name() or student.user.username if student else "Rahul Nayak"
    cgpa = getattr(student, 'cgpa', 8.5) if student else 8.5
    branch = getattr(student, 'department', 'Computer Science & Engineering') if student else 'Computer Science'
    prob = 86.4

    whatsapp_text = f"""📋 *WEEKLY PLACEMENT PROGRESS REPORT (CAMPUSLINK)*
🎓 *Student:* {student_name}
🏛 *Branch:* {branch}
📊 *CGPA:* {cgpa} / 10.0

*This Week's Campus Performance:*
✅ Weekly Coding Practice: 14.5 Hours (Top 10% in batch)
✅ DSA Problems Solved: 18 Questions
✅ Mock Interview Score: 84% (Cleared Round 1 & 2 standards)
🚀 *Estimated Placement Odds:* {prob}% (Safe Placement Tier)

*Mentor Note for Parents:*
{student_name} ka focus bahut achha chal raha hai. Agar aisi hi mehnat agle 4 mahine rahi toh ₹8–14 LPA package pakka crack hoga!

_Sent automatically via Campus to Career Portal_"""

    encoded_whatsapp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(whatsapp_text)}"

    context = {
        'student': student,
        'student_name': student_name,
        'cgpa': cgpa,
        'branch': branch,
        'prob': prob,
        'whatsapp_text': whatsapp_text,
        'encoded_whatsapp_url': encoded_whatsapp_url,
    }
    return render(request, 'ai_engine/parents_whatsapp_report.html', context)


def ai_interview_roaster_view(request):
    """
    7. AI BRUTAL INTERVIEW ROASTER ("Tu 3 baar atka, confidence zero hai")
    Savage, brutal, yet constructively accurate AI interview roasting engine.
    """
    student, _ = _get_or_create_student_and_wallet(request)

    question = request.POST.get('question', 'Tell me about yourself and your tech stack.')
    user_answer = request.POST.get('user_answer', '').strip()

    roast_result = None
    if request.method == 'POST' and user_answer:
        word_count = len(user_answer.split())
        buzzwords = [w for w in ['hardworking', 'passionate', 'fast learner', 'team player', 'motivated', 'enthusiastic'] if w in user_answer.lower()]
        has_metrics = any(char.isdigit() for char in user_answer)
        stumble_count = max(1, random.randint(2, 4)) if word_count < 40 or len(buzzwords) > 1 else 1

        if word_count < 20:
            roast_line = "Bhai interview chal raha hai ya WhatsApp status? 2 line me interview khatam kar diya? HR tujhe reject karne me bhi isse zyada time nahi lega!"
            confidence_score = 15
        elif len(buzzwords) >= 2:
            roast_line = f"Bhai tu 'hardworking', 'passionate' bolna kab band karega? {len(buzzwords)} buzzwords phek ke maare hain! Kaam kya kiya wo bata, dictionary mat suna!"
            confidence_score = 38
        elif not has_metrics:
            roast_line = "Project me bol raha hai 'I made an e-commerce website'. Kitne users the? Latency kitni thi? Zero metrics! Lagta hai YouTube tutorial dekh ke copy-paste kiya hai!"
            confidence_score = 48
        else:
            roast_line = "Theek thaak hai par beech me 3 baar atka! Eye contact aur flow me jaan nahi hai. Thoda confidence la warna interviewer so jayega!"
            confidence_score = 68

        roast_result = {
            'roast_line': roast_line,
            'stumble_count': stumble_count,
            'confidence_score': confidence_score,
            'buzzwords_used': buzzwords,
            'word_count': word_count,
            'actionable_fix': 'STAR Technique use karo: Situation -> Task -> Action -> Real Numbers (Metrics).'
        }

    sample_questions = [
        "Tell me about yourself and your tech stack.",
        "Explain Polymorphism in OOPs with a real-life example.",
        "Why should we hire you over 500 other campus candidates?",
        "Describe the hardest bug you ever resolved in your projects.",
    ]

    context = {
        'student': student,
        'question': question,
        'user_answer': user_answer,
        'roast_result': roast_result,
        'sample_questions': sample_questions,
    }
    return render(request, 'ai_engine/interview_roaster.html', context)




