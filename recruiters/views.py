
from datetime import datetime, timedelta, timezone as dt_timezone

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from jobs.models import Job
from applications.models import Application
from students.models import Skill
from accounts.decorators import role_required

@role_required('RECRUITER')
def recruiter_dashboard(request):
    try:
        profile = request.user.recruiter_profile
        company = profile.company
    except:
        company = None

    jobs = Job.objects.filter(company=company).prefetch_related('required_skills') if company else Job.objects.none()
    applications = Application.objects.filter(job__company=company).select_related('student__user', 'job') if company else Application.objects.none()

    context = {
        'active_jobs': len(jobs),
        'total_applicants': len(applications),
        'shortlisted': len([a for a in applications if a.status == 'SHORTLISTED']),
        'interviews': len([a for a in applications if a.status == 'INTERVIEW']),
        'jobs': jobs[:8],
        'recent_applicants': applications.order_by('-updated_at')[:8],
    }
    return render(request, 'recruiter/dashboard.html', context)


@role_required('RECRUITER')
def recruiter_job_create(request):
    try:
        company = request.user.recruiter_profile.company
    except Exception:
        messages.error(request, 'Only recruiters can create new jobs.')
        return redirect('home')

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        description = (request.POST.get('description') or '').strip()
        location = (request.POST.get('location') or '').strip()
        if not title or not description or not location:
            messages.error(request, 'Title, description, and location are required.')
            return render(request, 'recruiter/job_form.html', {'company': company, 'skills': Skill.objects.all(), 'now': timezone.now()})

        deadline_raw = request.POST.get('application_deadline')
        deadline = _parse_deadline(deadline_raw)
        if timezone.is_naive(deadline):
            deadline = deadline.replace(tzinfo=dt_timezone.utc)

        job = Job.objects.create(
            company=company,
            title=title,
            description=description,
            location=location,
            job_type=request.POST.get('job_type', 'Full-Time'),
            salary=request.POST.get('salary', ''),
            minimum_cgpa=float(request.POST.get('minimum_cgpa', 0) or 0),
            maximum_backlogs=int(request.POST.get('maximum_backlogs', 0) or 0),
            graduation_year=int(request.POST.get('graduation_year', 2026) or 2026),
            eligible_degree=request.POST.get('eligible_degree', '').strip(),
            experience_required=float(request.POST.get('experience_required', 0) or 0),
            required_programming_languages=request.POST.get('required_programming_languages', '').strip(),
            required_frameworks=request.POST.get('required_frameworks', '').strip(),
            required_technologies=request.POST.get('required_technologies', '').strip(),
            min_tenth=float(request.POST.get('min_tenth', 0) or 0),
            min_twelfth=float(request.POST.get('min_twelfth', 0) or 0),
            allowed_departments=request.POST.get('allowed_departments', ''),
            work_mode=request.POST.get('work_mode', 'Onsite'),
            internship_type=request.POST.get('internship_type', 'Full-Time'),
            application_deadline=deadline,
        )

        required_ids = request.POST.getlist('required_skills')
        preferred_ids = request.POST.getlist('preferred_skills')
        if required_ids:
            job.required_skills.set(Skill.objects.filter(id__in=required_ids))
        if preferred_ids:
            job.preferred_skills.set(Skill.objects.filter(id__in=preferred_ids))

        messages.success(request, 'Job posted successfully.')
        return redirect('recruiter_dashboard')

    return render(request, 'recruiter/job_form.html', {'company': company, 'skills': Skill.objects.all(), 'now': timezone.now()})


def _parse_deadline(value):
    if not value:
        return timezone.now() + timedelta(days=30)
    for date_format in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M'):
        try:
            deadline = datetime.strptime(value, date_format)
            return deadline.replace(tzinfo=dt_timezone.utc)
        except ValueError:
            continue
    return timezone.now() + timedelta(days=30)


@role_required('RECRUITER')
def recruiter_job_edit(request, job_id):
    company = get_object_or_404(request.user.recruiter_profile.company.__class__, pk=request.user.recruiter_profile.company_id)
    job = get_object_or_404(Job, id=job_id, company=company)
    if request.method == 'POST':
        job.title = (request.POST.get('title') or '').strip()
        job.description = (request.POST.get('description') or '').strip()
        job.location = (request.POST.get('location') or '').strip()
        job.salary = request.POST.get('salary', '')
        job.job_type = request.POST.get('job_type', 'Full-Time')
        job.work_mode = request.POST.get('work_mode', 'Onsite')
        job.minimum_cgpa = float(request.POST.get('minimum_cgpa', 0) or 0)
        job.maximum_backlogs = int(request.POST.get('maximum_backlogs', 0) or 0)
        job.graduation_year = int(request.POST.get('graduation_year', 2026) or 2026)
        job.eligible_degree = request.POST.get('eligible_degree', '').strip()
        job.experience_required = float(request.POST.get('experience_required', 0) or 0)
        job.required_programming_languages = request.POST.get('required_programming_languages', '').strip()
        job.required_frameworks = request.POST.get('required_frameworks', '').strip()
        job.required_technologies = request.POST.get('required_technologies', '').strip()
        job.application_deadline = _parse_deadline(request.POST.get('application_deadline'))
        job.save()
        job.required_skills.set(Skill.objects.filter(id__in=request.POST.getlist('required_skills')))
        job.preferred_skills.set(Skill.objects.filter(id__in=request.POST.getlist('preferred_skills')))
        messages.success(request, 'Job details updated.')
        return redirect('recruiter_dashboard')
    return render(request, 'recruiter/job_form.html', {
        'company': company,
        'job': job,
        'skills': Skill.objects.all(),
        'now': job.application_deadline,
    })


@role_required('RECRUITER')
def recruiter_application_status(request, application_id):
    if request.method != 'POST':
        return redirect('recruiter_dashboard')
    company = request.user.recruiter_profile.company
    application = get_object_or_404(Application, id=application_id, job__company=company)
    status = request.POST.get('status')
    valid_statuses = {choice[0] for choice in Application.STATUS_CHOICES}
    if status in valid_statuses:
        application.status = status
        application.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Application moved to {application.get_status_display()}.')
    return redirect('recruiter_dashboard')
