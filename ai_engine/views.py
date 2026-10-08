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
