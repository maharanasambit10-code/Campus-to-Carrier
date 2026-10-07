import json
from datetime import datetime, timezone as dt_timezone

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.decorators import pro_required
from applications.models import Application
from jobs.models import Job
from notifications.models import Notification
from .models import Interview, MockInterviewSession
from .services import (
    get_aria_greeting,
    get_interview_questions,
    evaluate_star_feedback,
    generate_aria_follow_up,
    generate_priya_interviewer_turn,
    synthesize_neural_tts,
    create_avatar_streaming_session,
    generate_mock_interview_report,
    has_neural_tts,
)


@login_required
def interview_list(request):
    if hasattr(request.user, 'student_profile'):
        interviews = Interview.objects.filter(application__student=request.user.student_profile)
    elif hasattr(request.user, 'recruiter_profile'):
        interviews = Interview.objects.filter(application__job__company=request.user.recruiter_profile.company)
    else:
        interviews = Interview.objects.all()
    interviews = interviews.select_related('application__student__user', 'application__job', 'application__job__company')

    membership = getattr(request.user, 'membership', None)
    is_pro = bool(membership and membership.is_active)
    mock_sessions = (
        MockInterviewSession.objects.filter(user=request.user, status='COMPLETED').order_by('-created_at')[:5]
        if is_pro else MockInterviewSession.objects.none()
    )

    return render(request, 'interviews/list.html', {
        'interviews': interviews,
        'scheduled_count': interviews.filter(status='SCHEDULED').count(),
        'completed_count': interviews.filter(status='COMPLETED').count(),
        'upcoming_interviews': interviews.filter(status='SCHEDULED'),
        'mock_sessions': mock_sessions,
        'is_pro': is_pro,
    })


@pro_required
def ai_mock_interview(request):
    """Interactive video mock interview room led by Priya & Nexus AI Robot."""
    membership = getattr(request.user, 'membership', None)
    is_pro = bool(membership and membership.is_active)
    profile = getattr(request.user, 'student_profile', None)
    student_name = request.user.first_name or request.user.username

    past_sessions = MockInterviewSession.objects.filter(user=request.user, status='COMPLETED').order_by('-created_at')[:5]

    # Fetch verified jobs available on CampusLink for job-wise practice
    jobs_qs = Job.objects.filter(is_verified=True).select_related('company').prefetch_related('required_skills').order_by('-created_at')[:40]
    available_jobs = []
    for j in jobs_qs:
        skills = [s.name for s in j.required_skills.all()]
        available_jobs.append({
            'id': j.id,
            'title': j.title,
            'company': j.company.name if j.company else 'Campus Partner',
            'location': j.location,
            'job_type': j.job_type,
            'work_mode': j.work_mode,
            'skills': skills,
            'description': j.description[:220] if j.description else '',
        })

    # Check if a specific job_id was requested via URL (e.g. from job detail page)
    selected_job_id = None
    raw_job_id = request.GET.get('job_id')
    if raw_job_id and raw_job_id.isdigit():
        selected_job_id = int(raw_job_id)

    return render(request, 'interviews/mock_room.html', {
        'student_name': student_name,
        'profile': profile,
        'is_pro': is_pro,
        'membership': membership,
        'past_sessions': past_sessions,
        'available_jobs': available_jobs,
        'available_jobs_json': json.dumps(available_jobs),
        'selected_job_id': selected_job_id,
        'has_neural_tts': has_neural_tts(),
    })


@pro_required
def api_start_mock_interview(request):
    """Initialize a new mock interview session and return job-tailored questions."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    membership = getattr(request.user, 'membership', None)
    is_pro = bool(membership and membership.is_active)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    job_id = data.get('job_id')
    role_target = data.get('role_target', 'Software Engineer Intern').strip()
    company_type = data.get('company_type', 'Tech Product Company').strip()
    interview_type = data.get('interview_type', 'HR').strip().upper()
    difficulty = data.get('difficulty', 'BEGINNER').strip().upper()
    try:
        duration_minutes = int(data.get('duration_minutes', 15))
    except (ValueError, TypeError):
        duration_minutes = 15

    student_name = request.user.first_name or request.user.username

    # If job_id was provided, verify and bind to that job
    job = None
    job_skills = []
    if job_id:
        try:
            job = Job.objects.filter(id=job_id).select_related('company').prefetch_related('required_skills').first()
            if job:
                role_target = job.title
                if job.company and job.company.name:
                    company_type = job.company.name
                job_skills = [s.name for s in job.required_skills.all()]
        except Exception:
            job = None

    questions = get_interview_questions(role_target, company_type, interview_type, difficulty, job_id=job_id, job=job)
    greeting = get_aria_greeting(student_name, role_target, company_type, interview_type, difficulty.title(), duration_minutes)

    session = MockInterviewSession.objects.create(
        user=request.user,
        role_target=role_target,
        company_type=company_type,
        interview_type=interview_type,
        difficulty=difficulty,
        duration_minutes=duration_minutes,
        status='IN_PROGRESS',
        transcript=[{'speaker': 'Priya', 'text': greeting, 'time': 0}]
    )

    return JsonResponse({
        'success': True,
        'session_id': session.pk,
        'greeting': greeting,
        'first_question': questions[0] if questions else "Tell me about yourself.",
        'questions': questions,
        'student_name': student_name,
        'is_pro': is_pro,
        'has_neural_tts': has_neural_tts(),
        'job_info': {
            'id': job.id if job else None,
            'title': role_target,
            'company': company_type,
            'skills': job_skills,
            'interview_type': interview_type,
            'difficulty': difficulty,
        }
    })


@pro_required
def api_aria_turn(request):
    """Handle student answer or control action and generate Priya's response."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    session_id = data.get('session_id')
    try:
        current_index = int(data.get('current_index', 0))
    except (ValueError, TypeError):
        current_index = 0

    student_answer = data.get('student_answer', '').strip()
    questions = data.get('questions', [])
    if not isinstance(questions, list) or not questions:
        questions = get_interview_questions('Software Engineer Intern', 'Tech Product Company', 'HR', 'BEGINNER')
    transcript = data.get('transcript', [])
    action = data.get('action', 'answer')
    if action == 'answer' and data.get('speechx_active') and data.get('speech_end') is not True:
        return JsonResponse({
            'success': False,
            'error': 'WAIT_FOR_SPEECH_END',
            'message': 'The response is still being transcribed.',
        }, status=409)
    if action == 'answer' and not student_answer:
        return JsonResponse({'success': False, 'error': 'Please provide an answer before continuing.'}, status=400)

    session = MockInterviewSession.objects.filter(pk=session_id, user=request.user).first()
    if not session:
        return JsonResponse({'success': False, 'error': 'Interview session not found.'}, status=404)
    role_target = session.role_target
    company_type = session.company_type
    interview_type = session.interview_type
    difficulty = session.difficulty
    user_name = request.user.first_name or request.user.username
    speech_metrics = data.get('speech_metrics', {})
    star_feedback = None

    emotion = "neutral"
    gesture = "none"
    internal_score_note = ""

    if action == 'repeat':
        current_q = questions[current_index] if current_index < len(questions) else "Tell me about yourself."
        aria_speech = f"Of course, let me repeat the question: {current_q}"
        next_q = current_q
        is_last = False
        next_index = current_index
        emotion = "smile"
        gesture = "nod"
    elif action == 'skip':
        next_index = current_index + 1
        is_last = next_index >= len(questions)
        next_q = questions[next_index] if not is_last else None
        if is_last:
            aria_speech = "No problem at all! That wraps up our questions. Let me generate your comprehensive performance feedback."
            emotion = "encouraging"
            gesture = "nod"
        else:
            aria_speech = f"Understood, let's move forward. Here is your next question: {next_q}"
            emotion = "neutral"
            gesture = "none"
    else:
        # Standard answer response
        next_index = current_index + 1
        is_last = next_index >= len(questions)
        next_q = questions[next_index] if not is_last else None

        current_q = questions[current_index] if current_index < len(questions) else ""
        turn_data = generate_priya_interviewer_turn(
            user_name=user_name,
            role_target=role_target,
            interview_type=interview_type,
            difficulty=difficulty,
            transcript=transcript,
            current_question=current_q,
            student_answer=student_answer,
            speech_metrics=speech_metrics,
            company_type=company_type
        )
        star_feedback = evaluate_star_feedback(student_answer, speech_metrics)
        follow_up = turn_data.get('speech_text', '')
        emotion = turn_data.get('emotion', 'encouraging')
        gesture = turn_data.get('gesture', 'nod')
        internal_score_note = turn_data.get('internal_score_note', '')

        if is_last:
            aria_speech = (
                f"{follow_up} That brings us to the close of our mock interview today! "
                "You communicated thoughtfully and demonstrated strong preparation. Let's review your performance feedback."
            )
        else:
            conversational_transitions = [
                f"{follow_up} Turning to our next topic: {next_q}",
                f"{follow_up} Let's explore: {next_q}",
                f"{follow_up} I'd love to hear your thoughts on: {next_q}",
                f"{follow_up} Building on that: {next_q}",
                f"{follow_up} Moving forward: {next_q}",
            ]
            aria_speech = conversational_transitions[current_index % len(conversational_transitions)]

        updated_questions = list(questions)
        next_difficulty = difficulty
        if next_q and star_feedback:
            difficulty_levels = ['BEGINNER', 'INTERMEDIATE', 'ADVANCED']
            level_index = difficulty_levels.index(difficulty) if difficulty in difficulty_levels else 0
            if star_feedback['score'] >= 3:
                level_index = min(level_index + 1, len(difficulty_levels) - 1)
            elif star_feedback['score'] <= 1:
                level_index = max(level_index - 1, 0)
            next_difficulty = difficulty_levels[level_index]
            if next_difficulty != difficulty:
                adaptive_questions = get_interview_questions(
                    role_target, company_type, interview_type, next_difficulty
                )
                previously_asked = set(updated_questions[:next_index])
                adaptive_question = next(
                    (question for question in adaptive_questions if question not in previously_asked),
                    next_q,
                )
                if next_index < len(updated_questions):
                    updated_questions[next_index] = adaptive_question
                else:
                    updated_questions.append(adaptive_question)
                next_q = adaptive_question
                session.difficulty = next_difficulty
                session.save(update_fields=['difficulty', 'updated_at'])
        else:
            updated_questions = list(questions)

    if action in {'repeat', 'skip'}:
        updated_questions = list(questions)

    return JsonResponse({
        'success': True,
        'aria_speech': aria_speech,
        'speech_text': aria_speech,
        'emotion': emotion,
        'gesture': gesture,
        'internal_score_note': internal_score_note,
        'star_feedback': star_feedback,
        'speech_metrics': star_feedback['metrics'] if star_feedback else {},
        'difficulty': session.difficulty,
        'questions': updated_questions,
        'next_question': next_q,
        'is_last': is_last,
        'next_index': next_index,
    })


@pro_required
def api_synthesize_tts(request):
    """Synthesize natural Indian-English female voice audio via Azure Speech / ElevenLabs."""
    text = request.GET.get('text', '').strip()
    if not text:
        return HttpResponse(status=400)
    audio_data = synthesize_neural_tts(text)
    if audio_data:
        audio_bytes, mime_type = audio_data
        return HttpResponse(audio_bytes, content_type=mime_type)
    return HttpResponse(status=204)  # No content -> client seamlessly uses local Web Speech


@pro_required
def api_avatar_session(request):
    """Negotiate or provide streaming WebRTC avatar session credentials (HeyGen / D-ID)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    provider = request.POST.get('provider', 'heygen')
    session_data = create_avatar_streaming_session(provider)
    return JsonResponse(session_data)


@pro_required
def api_finish_mock_interview(request):
    """Compute and save comprehensive feedback report for the session."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    session_id = data.get('session_id')
    transcript = data.get('transcript', [])
    observed_metrics = data.get('observed_metrics', {})

    session = MockInterviewSession.objects.filter(pk=session_id, user=request.user).first()
    if not session:
        session = MockInterviewSession.objects.create(
            user=request.user,
            status='COMPLETED'
        )

    report = generate_mock_interview_report(session, transcript, observed_metrics)

    session.overall_score = report['overall_score']
    session.communication_score = report['communication_score']
    session.content_score = report['content_score']
    session.confidence_score = report['confidence_score']
    session.body_language_score = report['body_language_score']
    session.strengths = report['strengths']
    session.areas_for_improvement = report['areas_for_improvement']
    session.sample_answer = report['sample_answer']
    session.practice_plan = report['practice_plan']
    session.transcript = transcript
    session.observations = report['observations']
    session.status = 'COMPLETED'
    session.save()

    return JsonResponse({
        'success': True,
        'session_id': session.pk,
        'report': {
            'overall_score': float(report['overall_score']),
            'communication_score': float(report['communication_score']),
            'content_score': float(report['content_score']),
            'confidence_score': float(report['confidence_score']),
            'body_language_score': float(report['body_language_score']),
            'strengths': report['strengths'],
            'areas_for_improvement': report['areas_for_improvement'],
            'sample_answer': report['sample_answer'],
            'practice_plan': report['practice_plan'],
            'observations': report['observations'],
            'big_tech_evaluation': report.get('big_tech_evaluation'),
        },
        'report_url': reverse('mock_interview_report', kwargs={'session_id': session.pk}),
    })


@pro_required
def mock_interview_report(request, session_id):
    """Render dedicated feedback and evaluation report for a mock interview."""
    session = get_object_or_404(MockInterviewSession, pk=session_id, user=request.user)
    return render(request, 'interviews/report.html', {
        'session': session,
        'strengths': session.strengths,
        'areas': session.areas_for_improvement,
        'practice_plan': session.practice_plan,
        'observations': session.observations,
        'transcript': session.transcript,
    })


@login_required
def schedule_interview(request, application_id):
    if not hasattr(request.user, 'recruiter_profile'):
        return redirect('dashboard_redirect')
    application = get_object_or_404(Application, id=application_id, job__company=request.user.recruiter_profile.company)
    if request.method == 'POST':
        scheduled_at = request.POST.get('scheduled_at')
        try:
            interview_time = datetime.fromisoformat(scheduled_at)
            if timezone.is_naive(interview_time):
                interview_time = interview_time.replace(tzinfo=dt_timezone.utc)
            interview = Interview.objects.create(
                application=application,
                round_name=request.POST.get('round_name', 'Technical Interview'),
                scheduled_at=interview_time,
                mode=request.POST.get('mode', 'ONLINE'),
                meeting_link=request.POST.get('meeting_link', ''),
                location=request.POST.get('location', ''),
            )
        except (TypeError, ValueError):
            messages.error(request, 'Enter a valid interview date and time.')
            return render(request, 'interviews/schedule.html', {'application': application})
        application.status = 'INTERVIEW'
        application.save(update_fields=['status', 'updated_at'])
        Notification.objects.create(user=application.student.user, title='Interview scheduled', message=f'{interview.round_name} for {application.job.title} is scheduled.', link='/interviews/')
        messages.success(request, 'Interview scheduled and the student was notified.')
        return redirect('recruiter_dashboard')
    return render(request, 'interviews/schedule.html', {'application': application})
