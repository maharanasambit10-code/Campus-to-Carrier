from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from .models import Job
from companies.models import Company, CompanyConnection
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
    company_type = request.GET.get('company_type', '').strip()
    company_id = request.GET.get('company_id', '').strip()
    active_tab = request.GET.get('tab', 'jobs').strip()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company__name__icontains=query) |
            Q(company__industry__icontains=query) |
            Q(location__icontains=query) |
            Q(required_skills__name__icontains=query)
        ).distinct()
    if role:
        jobs = jobs.filter(required_skills__name__icontains=role).distinct()
    if location:
        jobs = jobs.filter(location__icontains=location)
    if job_type:
        jobs = jobs.filter(job_type__icontains=job_type)
    if company_type:
        jobs = jobs.filter(company__company_type__iexact=company_type)
    if company_id:
        jobs = jobs.filter(company_id=company_id)
    if experience == 'fresher':
        jobs = jobs.filter(minimum_cgpa__lte=7.0)
    elif experience == '0-1':
        jobs = jobs.filter(minimum_cgpa__lte=8.0)

    jobs = list(jobs)
    profile = getattr(request.user, 'student_profile', None)

    if profile:
        matches = match_jobs(profile, jobs)
    else:
        matches = [
            {
                'job': job,
                'score': 0,
                'matched_skills': [],
                'missing_skills': list(job.required_skills.values_list('name', flat=True)),
                'eligible': True,
            }
            for job in jobs
        ]

    applied_ids = set()
    connected_company_ids = set()
    if profile:
        applied_ids = set(
            Application.objects.filter(student=profile, job_id__in=[job.id for job in jobs]).values_list('job_id', flat=True)
        )
        connected_company_ids = set(
            CompanyConnection.objects.filter(student=profile).values_list('company_id', flat=True)
        )

    # Startups and Companies directory data
    companies_qs = Company.objects.annotate(
        total_jobs=Count('jobs')
    ).order_by('-total_jobs', 'name')
    if query:
        companies_qs = companies_qs.filter(
            Q(name__icontains=query) |
            Q(industry__icontains=query) |
            Q(tech_stack__icontains=query) |
            Q(locations__icontains=query)
        )
    if company_type:
        companies_qs = companies_qs.filter(company_type__iexact=company_type)

    companies_list = list(companies_qs)

    context = {
        'job_matches': matches,
        'applied_ids': applied_ids,
        'connected_company_ids': connected_company_ids,
        'companies': companies_list,
        'active_tab': active_tab,
        'query': query,
        'selected_role': role,
        'selected_experience': experience,
        'selected_location': location,
        'selected_job_type': job_type,
        'selected_company_type': company_type,
        'selected_company_id': company_id,
        'role_filters': ['Python', 'AI', 'Machine Learning', 'Data Science', 'Backend', 'React', 'Go', 'Cloud'],
        'location_filters': ['Bhubaneswar', 'Bengaluru', 'Hyderabad', 'Pune', 'Mumbai', 'Remote'],
        'company_types': ['Startup', 'Unicorn', 'Enterprise', 'Product Lab'],
        'student_profile': profile,
    }
    return render(request, 'student/jobs.html', context)


@login_required
def job_detail(request, job_id):
    job = get_object_or_404(
        Job.objects.select_related('company').prefetch_related('required_skills', 'preferred_skills'),
        id=job_id
    )
    application = None
    profile = getattr(request.user, 'student_profile', None)
    is_connected = False

    if profile:
        application = Application.objects.filter(student=profile, job=job).first()
        is_connected = CompanyConnection.objects.filter(student=profile, company=job.company).exists()

    # Pre-calculated match for single job if student
    match_score = None
    if profile:
        match_res = match_jobs(profile, [job])
        if match_res:
            match_score = match_res[0]

    context = {
        'job': job,
        'application': application,
        'student_profile': profile,
        'is_connected': is_connected,
        'match_score': match_score,
    }
    return render(request, 'student/job_detail.html', context)


@login_required
def apply_job(request, job_id):
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only registered students can apply for jobs.")
        return redirect('student_dashboard')

    job = get_object_or_404(Job.objects.select_related('company'), id=job_id)
    profile = request.user.student_profile
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1'

    # Check deadline
    if job.application_deadline and job.application_deadline < timezone.now():
        msg = 'This opportunity is no longer accepting applications (deadline passed).'
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect('job_detail', job_id=job.id)

    # Check if already applied
    existing_app = Application.objects.filter(student=profile, job=job).first()

    # GET Request: Show dedicated full-page application form
    if request.method == 'GET':
        context = {
            'job': job,
            'profile': profile,
            'existing_application': existing_app,
        }
        return render(request, 'student/job_apply.html', context)

    # POST Request: Process and save form submission
    if existing_app:
        msg = f"You have already applied for {job.title} at {job.company.name}."
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg, 'already_applied': True})
        messages.warning(request, msg)
        return redirect('student_applications')

    full_name = request.POST.get('full_name', '').strip() or request.user.get_full_name() or request.user.username
    email = request.POST.get('email', '').strip() or request.user.email
    phone = request.POST.get('phone', '').strip() or profile.phone
    degree_major = request.POST.get('degree_major', '').strip() or profile.degree or profile.department
    college = request.POST.get('college', '').strip() or profile.college
    cgpa_raw = request.POST.get('cgpa', '').strip()
    try:
        cgpa_val = float(cgpa_raw) if cgpa_raw else profile.cgpa
    except (ValueError, TypeError):
        cgpa_val = profile.cgpa

    portfolio_url = request.POST.get('portfolio_url', '').strip() or profile.portfolio
    github_url = request.POST.get('github_url', '').strip() or profile.github
    linkedin_url = request.POST.get('linkedin_url', '').strip() or profile.linkedin
    cover_letter = request.POST.get('cover_letter', '').strip()
    availability = request.POST.get('availability', 'Immediate').strip()
    expected_salary = request.POST.get('expected_salary', '').strip()
    experience_level = request.POST.get('experience_level', 'Fresher').strip()
    custom_resume = request.FILES.get('custom_resume')

    # Create application with complete form data
    application = Application.objects.create(
        student=profile,
        job=job,
        full_name=full_name,
        email=email,
        phone=phone,
        degree_major=degree_major,
        college=college,
        cgpa=cgpa_val,
        portfolio_url=portfolio_url,
        github_url=github_url,
        linkedin_url=linkedin_url,
        cover_letter=cover_letter,
        availability=availability,
        expected_salary=expected_salary,
        experience_level=experience_level,
        custom_resume=custom_resume,
    )

    success_msg = f"Your application for {job.title} at {job.company.name} has been submitted successfully!"

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': success_msg,
            'job_id': job.id,
            'job_title': job.title,
            'company': job.company.name,
            'application_id': application.id,
        })

    messages.success(request, success_msg)
    return redirect('student_applications')


@login_required
def connect_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1'

    if not hasattr(request.user, 'student_profile'):
        msg = 'Only registered students can connect with companies.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg}, status=403)
        messages.error(request, msg)
        return redirect('job_list')

    profile = request.user.student_profile
    conn, created = CompanyConnection.objects.get_or_create(
        student=profile,
        company=company,
        defaults={
            'preferred_role': request.POST.get('preferred_role', '').strip(),
            'note': request.POST.get('note', '').strip(),
        }
    )

    if not created and request.POST.get('action') == 'disconnect':
        conn.delete()
        msg = f"Disconnected from {company.name}."
        if is_ajax:
            return JsonResponse({'success': True, 'connected': False, 'message': msg})
        messages.info(request, msg)
        return redirect(request.META.get('HTTP_REFERER') or 'job_list')

    msg = f"Successfully connected with {company.name}! Founders and recruiters can now review your profile for opportunities."
    if is_ajax:
        return JsonResponse({
            'success': True,
            'connected': True,
            'company_id': company.id,
            'company_name': company.name,
            'message': msg,
        })

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER') or 'job_list')
