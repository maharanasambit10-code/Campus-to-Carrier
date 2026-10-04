from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from students.models import StudentProfile

from .models import Course, CourseApplication


def _student_profile(request):
    if request.user.role != 'STUDENT':
        return None
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    return profile


@login_required
def course_list(request):
    courses = Course.objects.filter(is_published=True).select_related('provider')
    query = request.GET.get('q', '').strip()
    if query:
        courses = courses.filter(title__icontains=query) | courses.filter(provider__name__icontains=query)

    profile = _student_profile(request)
    applied_ids = set()
    if profile:
        applied_ids = set(
            CourseApplication.objects.filter(student=profile, course__in=courses)
            .values_list('course_id', flat=True)
        )
    return render(request, 'courses/list.html', {
        'courses': courses,
        'query': query,
        'applied_ids': applied_ids,
    })


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course.objects.select_related('provider'), id=course_id, is_published=True)
    application = None
    profile = _student_profile(request)
    if profile:
        application = CourseApplication.objects.filter(student=profile, course=course).first()
    return render(request, 'courses/detail.html', {'course': course, 'application': application})


@login_required
def apply_course(request, course_id):
    if request.method != 'POST':
        return redirect('course_detail', course_id=course_id)

    profile = _student_profile(request)
    if profile is None:
        messages.error(request, 'Only students can apply for courses.')
        return redirect('dashboard_redirect')

    course = get_object_or_404(Course, id=course_id, is_published=True)
    if course.deadline and course.deadline < timezone.now():
        messages.error(request, 'This course is no longer accepting applications.')
    else:
        application, created = CourseApplication.objects.get_or_create(student=profile, course=course)
        if created:
            messages.success(request, 'Course application submitted successfully.')
        else:
            messages.warning(request, 'You have already applied for this course.')
    return redirect('course_detail', course_id=course.id)


@login_required
def course_applications(request):
    profile = _student_profile(request)
    if profile is None:
        messages.error(request, 'Only students can view course applications.')
        return redirect('dashboard_redirect')
    applications = CourseApplication.objects.filter(student=profile).select_related('course', 'course__provider')
    return render(request, 'courses/applications.html', {'applications': applications})
