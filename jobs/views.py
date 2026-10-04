
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Job
from applications.models import Application
from ai_engine.services import match_jobs

@login_required
def job_list(request):
    jobs = Job.objects.select_related('company').prefetch_related('required_skills').order_by('-created_at')
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    experience = request.GET.get('experience', '').strip()
    location = request.GET.get('location', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(company__name__icontains=query) | Q(location__icontains=query) | Q(required_skills__name__icontains=query)).distinct()
    if role:
        jobs = jobs.filter(required_skills__name__icontains=role).distinct()
    if location:
        jobs = jobs.filter(location__icontains=location)
    if job_type:
        jobs = jobs.filter(job_type__icontains=job_type)
    if experience == 'fresher':
        jobs = jobs.filter(minimum_cgpa__lte=7)
    elif experience == '0-1':
        jobs = jobs.filter(minimum_cgpa__lte=8)

    jobs = list(jobs)
    if hasattr(request.user, 'student_profile'):
        matches = match_jobs(request.user.student_profile, jobs)
    else:
        matches = [{'job': job, 'score': 0, 'matched_skills': [], 'missing_skills': list(job.required_skills.values_list('name', flat=True)), 'eligible': True} for job in jobs]
    applied_ids = set()
    if hasattr(request.user, 'student_profile'):
        applied_ids = set(Application.objects.filter(student=request.user.student_profile, job_id__in=[job.id for job in jobs]).values_list('job_id', flat=True))
    context = {
        'job_matches': matches,
        'applied_ids': applied_ids,
        'query': query,
        'selected_role': role,
        'selected_experience': experience,
        'selected_location': location,
        'selected_job_type': job_type,
        'role_filters': ['Python', 'AI', 'Machine Learning', 'Data Science', 'Backend'],
        'location_filters': ['Bhubaneswar', 'Bengaluru', 'Hyderabad', 'Pune', 'Remote'],
    }
    return render(request, 'student/jobs.html', context)


@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job.objects.select_related('company').prefetch_related('required_skills'), id=job_id)
    application = None
    if hasattr(request.user, 'student_profile'):
        application = Application.objects.filter(student=request.user.student_profile, job=job).first()
    return render(request, 'student/job_detail.html', {'job': job, 'application': application})

@login_required
def apply_job(request, job_id):
    if request.method != 'POST':
        return redirect('job_detail', job_id=job_id)
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can apply for jobs.")
        return redirect('student_dashboard')
        
    job = get_object_or_404(Job, id=job_id)
    profile = request.user.student_profile

    if job.application_deadline and job.application_deadline < timezone.now():
        messages.error(request, 'This opportunity is no longer accepting applications.')
        return redirect('job_detail', job_id=job.id)

    # Check duplicate
    if Application.objects.filter(student=profile, job=job).exists():
        messages.warning(request, "You have already applied for this job.")
    else:
        Application.objects.create(student=profile, job=job)
        messages.success(request, 'Application submitted successfully.')
        
    return redirect('student_applications')
