import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from students.models import StudentProfile

from .models import (
    LearningCourse, Lesson, Quiz, QuizQuestion,
    CourseEnrollment, LessonProgress, QuizAttempt, Certificate,
    Course, CourseApplication,
)


# ── helpers ─────────────────────────────────────────────────────────────────────

def _get_student(request):
    """Return StudentProfile for the logged-in student, or None."""
    try:
        if request.user.role != 'STUDENT':
            return None
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        return profile
    except Exception:
        return None


def _enrollment_context(student, course):
    """Return dict with enrollment data for a student + course."""
    if not student:
        return {'enrollment': None, 'progress': 0, 'completed_lessons': set()}
    enrollment = CourseEnrollment.objects.filter(student=student, course=course).first()
    if not enrollment:
        return {'enrollment': None, 'progress': 0, 'completed_lessons': set()}
    completed_ids = set(
        LessonProgress.objects.filter(enrollment=enrollment, completed=True)
        .values_list('lesson_id', flat=True)
    )
    return {
        'enrollment': enrollment,
        'progress': enrollment.progress_percent(),
        'completed_lessons': completed_ids,
    }


# ── Learning Hub Dashboard (replaces old course_list) ───────────────────────────

@login_required
def learning_hub(request):
    """Main Learning Hub dashboard."""
    student = _get_student(request)
    query    = request.GET.get('q', '').strip()
    category = request.GET.get('category', 'all')

    courses = LearningCourse.objects.filter(is_published=True)
    if query:
        courses = courses.filter(title__icontains=query)
    if category and category != 'all':
        courses = courses.filter(category=category)

    # per-course progress for this student
    course_data = []
    enrolled_ids = set()
    completed_count = 0
    cert_count = 0

    if student:
        enrollments = {
            e.course_id: e
            for e in CourseEnrollment.objects.filter(student=student).select_related('course')
        }
        enrolled_ids = set(enrollments.keys())

        for c in courses:
            enr = enrollments.get(c.id)
            prog = enr.progress_percent() if enr else 0
            has_cert = False
            if enr:
                has_cert = Certificate.objects.filter(enrollment=enr).exists()
                if enr.completed:
                    completed_count += 1
                if has_cert:
                    cert_count += 1
            course_data.append({
                'course': c,
                'enrolled': enr is not None,
                'progress': prog,
                'has_cert': has_cert,
                'enrollment': enr,
            })
    else:
        for c in courses:
            course_data.append({
                'course': c,
                'enrolled': False,
                'progress': 0,
                'has_cert': False,
                'enrollment': None,
            })

    total_courses = LearningCourse.objects.filter(is_published=True).count()
    overall_progress = 0
    if student and enrolled_ids:
        progresses = [
            CourseEnrollment.objects.get(student=student, course_id=cid).progress_percent()
            for cid in enrolled_ids
        ]
        overall_progress = int(sum(progresses) / len(progresses)) if progresses else 0

    from .models import CATEGORY_CHOICES
    return render(request, 'courses/learning_hub.html', {
        'course_data': course_data,
        'query': query,
        'selected_category': category,
        'category_choices': CATEGORY_CHOICES,
        'total_courses': total_courses,
        'enrolled_count': len(enrolled_ids),
        'completed_count': completed_count,
        'cert_count': cert_count,
        'overall_progress': overall_progress,
        'student': student,
    })


# ── Course Detail ────────────────────────────────────────────────────────────────

@login_required
def hub_course_detail(request, course_slug):
    """Course detail: description, objectives, lesson list."""
    course  = get_object_or_404(LearningCourse, slug=course_slug, is_published=True)
    student = _get_student(request)
    ctx     = _enrollment_context(student, course)

    lessons = course.lessons.filter(is_published=True)
    try:
        quiz = course.quiz
    except Quiz.DoesNotExist:
        quiz = None

    last_attempt = None
    if ctx['enrollment'] and quiz:
        last_attempt = QuizAttempt.objects.filter(enrollment=ctx['enrollment']).first()

    cert = None
    if ctx['enrollment']:
        cert = Certificate.objects.filter(enrollment=ctx['enrollment']).first()

    ctx.update({
        'course': course,
        'lessons': lessons,
        'quiz': quiz,
        'last_attempt': last_attempt,
        'certificate': cert,
        'student': student,
    })
    return render(request, 'courses/hub_course_detail.html', ctx)


# ── Enroll ──────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def enroll_course(request, course_slug):
    student = _get_student(request)
    if not student:
        messages.error(request, 'Only students can enroll in courses.')
        return redirect('learning_hub')

    course = get_object_or_404(LearningCourse, slug=course_slug, is_published=True)
    _, created = CourseEnrollment.objects.get_or_create(student=student, course=course)
    if created:
        messages.success(request, f'You are now enrolled in "{course.title}"!')
    else:
        messages.info(request, f'You are already enrolled in "{course.title}".')
    return redirect('hub_course_detail', course_slug=course_slug)


# ── Lesson View ─────────────────────────────────────────────────────────────────

@login_required
def hub_lesson(request, course_slug, lesson_id):
    """Display a single lesson."""
    course  = get_object_or_404(LearningCourse, slug=course_slug, is_published=True)
    lesson  = get_object_or_404(Lesson, id=lesson_id, course=course, is_published=True)
    student = _get_student(request)

    enrollment = None
    if student:
        enrollment = CourseEnrollment.objects.filter(student=student, course=course).first()
        if not enrollment:
            messages.warning(request, 'Please enroll in the course first.')
            return redirect('hub_course_detail', course_slug=course_slug)

    lessons_qs = list(course.lessons.filter(is_published=True))
    idx        = next((i for i, l in enumerate(lessons_qs) if l.id == lesson.id), 0)
    prev_lesson = lessons_qs[idx - 1] if idx > 0 else None
    next_lesson = lessons_qs[idx + 1] if idx < len(lessons_qs) - 1 else None

    # already completed?
    lp = None
    if enrollment:
        lp = LessonProgress.objects.filter(enrollment=enrollment, lesson=lesson).first()

    completed_ids = set()
    if enrollment:
        completed_ids = set(
            LessonProgress.objects.filter(enrollment=enrollment, completed=True)
            .values_list('lesson_id', flat=True)
        )

    return render(request, 'courses/hub_lesson.html', {
        'course': course,
        'lesson': lesson,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'enrollment': enrollment,
        'lesson_progress': lp,
        'completed_ids': completed_ids,
        'all_lessons': lessons_qs,
        'current_index': idx,
    })


# ── Mark Lesson Complete ─────────────────────────────────────────────────────────

@login_required
@require_POST
def mark_lesson_complete(request, course_slug, lesson_id):
    student = _get_student(request)
    if not student:
        return JsonResponse({'error': 'Not a student'}, status=403)

    course     = get_object_or_404(LearningCourse, slug=course_slug)
    lesson     = get_object_or_404(Lesson, id=lesson_id, course=course)
    enrollment = get_object_or_404(CourseEnrollment, student=student, course=course)

    lp, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    if not lp.completed:
        lp.completed    = True
        lp.completed_at = timezone.now()
        lp.save()

    # Check if course is fully completed now
    total     = course.lessons.filter(is_published=True).count()
    done      = LessonProgress.objects.filter(enrollment=enrollment, completed=True).count()
    progress  = int((done / total) * 100) if total else 0

    if progress == 100 and not enrollment.completed:
        enrollment.completed    = True
        enrollment.completed_at = timezone.now()
        enrollment.save()

        # Auto-award certificate if quiz passed or no quiz
        try:
            quiz = course.quiz
            passed = QuizAttempt.objects.filter(enrollment=enrollment, passed=True).exists()
        except Quiz.DoesNotExist:
            passed = True  # no quiz required

        if passed:
            Certificate.objects.get_or_create(enrollment=enrollment)

    return JsonResponse({'progress': progress, 'done': done, 'total': total})


# ── Quiz ─────────────────────────────────────────────────────────────────────────

@login_required
def hub_quiz(request, course_slug):
    """Display the quiz for a course."""
    course  = get_object_or_404(LearningCourse, slug=course_slug, is_published=True)
    student = _get_student(request)
    enrollment = None
    if student:
        enrollment = CourseEnrollment.objects.filter(student=student, course=course).first()
    if not enrollment:
        messages.warning(request, 'Enroll in the course to take the quiz.')
        return redirect('hub_course_detail', course_slug=course_slug)

    try:
        quiz = course.quiz
    except Quiz.DoesNotExist:
        messages.info(request, 'No quiz available for this course yet.')
        return redirect('hub_course_detail', course_slug=course_slug)

    questions = quiz.questions.all()
    last_attempt = QuizAttempt.objects.filter(enrollment=enrollment).first()

    return render(request, 'courses/hub_quiz.html', {
        'course': course,
        'quiz': quiz,
        'questions': questions,
        'enrollment': enrollment,
        'last_attempt': last_attempt,
    })


@login_required
@require_POST
def hub_quiz_submit(request, course_slug):
    """Process quiz submission."""
    student = _get_student(request)
    if not student:
        return redirect('learning_hub')

    course     = get_object_or_404(LearningCourse, slug=course_slug)
    enrollment = get_object_or_404(CourseEnrollment, student=student, course=course)

    try:
        quiz = course.quiz
    except Quiz.DoesNotExist:
        return redirect('hub_course_detail', course_slug=course_slug)

    questions = quiz.questions.all()
    answers   = {}
    score     = 0

    for q in questions:
        selected = request.POST.get(f'q_{q.id}', '').strip().upper()
        answers[str(q.id)] = selected
        if selected == q.answer:
            score += 1

    total  = questions.count()
    pct    = int((score / total) * 100) if total else 0
    passed = pct >= quiz.pass_percent

    attempt = QuizAttempt.objects.create(
        enrollment=enrollment,
        score=score,
        total=total,
        passed=passed,
        answers=answers,
    )

    # Award certificate if all lessons done + quiz passed
    if passed and enrollment.completed:
        Certificate.objects.get_or_create(enrollment=enrollment)

    return redirect('hub_quiz_result', course_slug=course_slug, attempt_id=attempt.id)


@login_required
def hub_quiz_result(request, course_slug, attempt_id):
    """Show quiz result with correct answers."""
    course  = get_object_or_404(LearningCourse, slug=course_slug)
    student = _get_student(request)
    enrollment = get_object_or_404(CourseEnrollment, student=student, course=course)
    attempt    = get_object_or_404(QuizAttempt, id=attempt_id, enrollment=enrollment)

    questions  = attempt.enrollment.course.quiz.questions.all()
    cert       = Certificate.objects.filter(enrollment=enrollment).first()

    question_results = []
    for q in questions:
        selected  = attempt.answers.get(str(q.id), '')
        is_correct = selected == q.answer
        question_results.append({
            'question': q,
            'selected': selected,
            'is_correct': is_correct,
        })

    return render(request, 'courses/hub_quiz_result.html', {
        'course': course,
        'attempt': attempt,
        'question_results': question_results,
        'certificate': cert,
    })


# ── My Progress ──────────────────────────────────────────────────────────────────

@login_required
def hub_my_progress(request):
    """Student's personal progress dashboard."""
    student = _get_student(request)
    if not student:
        messages.error(request, 'Only students can view progress.')
        return redirect('learning_hub')

    enrollments = CourseEnrollment.objects.filter(student=student).select_related('course')
    certs       = Certificate.objects.filter(enrollment__student=student).select_related('enrollment__course')

    progress_data = []
    for enr in enrollments:
        attempts = QuizAttempt.objects.filter(enrollment=enr).first()
        cert     = Certificate.objects.filter(enrollment=enr).first()
        progress_data.append({
            'enrollment': enr,
            'course': enr.course,
            'progress': enr.progress_percent(),
            'quiz_attempt': attempts,
            'certificate': cert,
        })

    return render(request, 'courses/hub_progress.html', {
        'progress_data': progress_data,
        'certificates': certs,
        'student': student,
    })


# ── Certificate View ─────────────────────────────────────────────────────────────

@login_required
def hub_certificate(request, cert_uuid):
    """View / print a certificate."""
    cert = get_object_or_404(Certificate, certificate_id=cert_uuid)
    # Allow owner or superuser only
    if not (request.user.is_superuser or cert.student.user == request.user):
        messages.error(request, 'You do not have permission to view this certificate.')
        return redirect('learning_hub')
    return render(request, 'courses/hub_certificate.html', {'cert': cert})


# ── Legacy views (kept for old URLs) ────────────────────────────────────────────

@login_required
def course_list(request):
    return redirect('learning_hub')


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    return render(request, 'courses/detail.html', {'course': course, 'application': None})


@login_required
def apply_course(request, course_id):
    if request.method != 'POST':
        return redirect('course_detail', course_id=course_id)
    student = _get_student(request)
    if student is None:
        messages.error(request, 'Only students can apply for courses.')
        return redirect('dashboard_redirect')
    course = get_object_or_404(Course, id=course_id, is_published=True)
    application, created = CourseApplication.objects.get_or_create(student=student, course=course)
    if created:
        messages.success(request, 'Course application submitted.')
    else:
        messages.warning(request, 'Already applied.')
    return redirect('course_detail', course_id=course.id)


@login_required
def course_applications(request):
    student = _get_student(request)
    if student is None:
        messages.error(request, 'Only students can view course applications.')
        return redirect('dashboard_redirect')
    applications = CourseApplication.objects.filter(student=student).select_related('course', 'course__provider')
    return render(request, 'courses/applications.html', {'applications': applications})
