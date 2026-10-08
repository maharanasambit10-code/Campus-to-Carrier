import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
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


