import json
from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST

from .models import Job, SavedJob
from .services import calculate_resume_job_match, EXPANDED_SKILL_KEYWORDS
from companies.models import Company, CompanyConnection
from applications.models import Application
from students.models import Skill


POPULAR_FILTER_SKILLS = [
    'Python', 'Java', 'C++', 'JavaScript', 'React', 'Node.js',
    'Django', 'Spring Boot', 'SQL', 'MySQL', 'MongoDB', 'AWS',
    'Azure', 'GCP', 'Docker', 'Kubernetes', 'Machine Learning',
    'Data Science', 'Data Analytics', 'Power BI', 'Tableau',
    'DevOps', 'Git', 'DSA', 'AI'
]


@login_required
def job_list(request):
    jobs_qs = Job.objects.filter(is_active=True, is_verified=True).select_related('company').prefetch_related('required_skills').order_by('-created_at')

    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    location = request.GET.get('location', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    work_mode = request.GET.get('work_mode', '').strip()
    company_type = request.GET.get('company_type', '').strip()
    company_id = request.GET.get('company_id', '').strip()
    experience = request.GET.get('experience', '').strip()
    active_tab = request.GET.get('tab', 'jobs').strip()

    # Multi-skill filtering support: can be passed via ?skills=Python,SQL or multiple ?skills=Python&skills=SQL
    skills_param = request.GET.getlist('skills')
    selected_skills = []
    if skills_param:
        for s in skills_param:
            for part in s.split(','):
                cleaned = part.strip()
                if cleaned and cleaned not in selected_skills:
                    selected_skills.append(cleaned)
    elif request.GET.get('skill'):
        selected_skills = [request.GET.get('skill').strip()]

    # Global search across title, company, industry, location, skills, description
    if query:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=query) |
            Q(company__name__icontains=query) |
            Q(company__industry__icontains=query) |
            Q(location__icontains=query) |
            Q(required_skills__name__icontains=query) |
            Q(required_programming_languages__icontains=query) |
            Q(required_frameworks__icontains=query) |
            Q(required_technologies__icontains=query) |
            Q(description__icontains=query)
        ).distinct()

    # Apply Multi-skill filtering (every selected skill should be represented in the job)
    if selected_skills:
        for sk in selected_skills:
            jobs_qs = jobs_qs.filter(
                Q(required_skills__name__iexact=sk) |
                Q(required_skills__name__icontains=sk) |
                Q(required_programming_languages__icontains=sk) |
                Q(required_frameworks__icontains=sk) |
                Q(required_technologies__icontains=sk) |
                Q(description__icontains=sk)
            ).distinct()

    if role:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=role) |
            Q(required_skills__name__icontains=role)
        ).distinct()

    if location:
        jobs_qs = jobs_qs.filter(location__icontains=location)

    if job_type:
        jobs_qs = jobs_qs.filter(job_type__iexact=job_type)

    if work_mode:
        jobs_qs = jobs_qs.filter(work_mode__iexact=work_mode)

    if company_type:
        jobs_qs = jobs_qs.filter(company__company_type__iexact=company_type)

    if company_id:
        jobs_qs = jobs_qs.filter(company_id=company_id)

    if experience == 'fresher':
        jobs_qs = jobs_qs.filter(Q(experience_required=0) | Q(experience_text__icontains='fresher'))
    elif experience == '0-1':
        jobs_qs = jobs_qs.filter(experience_required__lte=1.0)
    elif experience == '1-3':
        jobs_qs = jobs_qs.filter(experience_required__gte=1.0, experience_required__lte=3.0)
    elif experience == '3+':
        jobs_qs = jobs_qs.filter(experience_required__gte=3.0)

    jobs = list(jobs_qs)
    profile = getattr(request.user, 'student_profile', None)

    # Compute live match data for each job
    matches = []
    for job in jobs:
        match_info = calculate_resume_job_match(job, student_profile=profile)
        matches.append({
            'job': job,
            'score': match_info['match_percentage'],
            'matched_skills': match_info['matched_skills'],
            'missing_skills': match_info['missing_skills'],
            'recommended_skills': match_info['recommended_skills'],
            'eligible': True,
        })

    applied_ids = set()
    connected_company_ids = set()
    saved_job_ids = set()

    if profile:
        job_ids = [job.id for job in jobs]
        applied_ids = set(
            Application.objects.filter(student=profile, job_id__in=job_ids).values_list('job_id', flat=True)
        )
        connected_company_ids = set(
            CompanyConnection.objects.filter(student=profile).values_list('company_id', flat=True)
        )
        saved_job_ids = set(
            SavedJob.objects.filter(student=profile, job_id__in=job_ids).values_list('job_id', flat=True)
        )

    # Startups and Companies directory tab data
    companies_qs = Company.objects.annotate(
        total_jobs=Count('jobs', filter=Q(jobs__is_active=True, jobs__is_verified=True))
    ).order_by('-total_jobs', 'name')

    if query:
        companies_qs = companies_qs.filter(
            Q(name__icontains=query) |
            Q(industry__icontains=query) |
            Q(tech_stack__icontains=query) |
            Q(locations__icontains=query) |
            Q(headquarters__icontains=query)
        )
    if company_type:
        companies_qs = companies_qs.filter(company_type__iexact=company_type)

    context = {
        'job_matches': matches,
        'applied_ids': applied_ids,
        'connected_company_ids': connected_company_ids,
        'saved_job_ids': saved_job_ids,
        'companies': list(companies_qs),
        'active_tab': active_tab,
        'query': query,
        'selected_role': role,
        'selected_skills': selected_skills,
        'selected_experience': experience,
        'selected_location': location,
        'selected_job_type': job_type,
        'selected_work_mode': work_mode,
        'selected_company_type': company_type,
        'selected_company_id': company_id,
        'popular_skills': POPULAR_FILTER_SKILLS,
        'role_filters': ['Software Development', 'Data Science', 'AI / ML Engineer', 'Cloud / DevOps', 'Frontend Developer', 'Backend Developer', 'Full Stack', 'Cybersecurity'],
        'location_filters': ['Bhubaneswar', 'Bengaluru', 'Hyderabad', 'Pune', 'Noida', 'Mumbai', 'Remote'],
        'company_types': ['Enterprise', 'Unicorn', 'Startup', 'Product Lab'],
        'work_modes': ['Onsite', 'Hybrid', 'Remote'],
        'job_types': ['Full-Time', 'Internship', 'Contract'],
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
    is_saved = False

    if profile:
        application = Application.objects.filter(student=profile, job=job).first()
        is_connected = CompanyConnection.objects.filter(student=profile, company=job.company).exists()
        is_saved = SavedJob.objects.filter(student=profile, job=job).exists()

    match_info = calculate_resume_job_match(job, student_profile=profile)

    context = {
        'job': job,
        'application': application,
        'student_profile': profile,
        'is_connected': is_connected,
        'is_saved': is_saved,
        'match_info': match_info,
        'score': match_info['match_percentage'],
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
        msg = 'This opportunity is no longer accepting applications (application deadline has passed).'
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect('job_detail', job_id=job.id)

    # Check if already applied
    existing_app = Application.objects.filter(student=profile, job=job).first()

    # GET Request: Show dedicated full-page application view
    if request.method == 'GET':
        match_info = calculate_resume_job_match(job, student_profile=profile)
        context = {
            'job': job,
            'profile': profile,
            'existing_application': existing_app,
            'match_info': match_info,
        }
        return render(request, 'student/job_apply.html', context)

    # POST Request: Process and save form submission
    if existing_app:
        msg = f"You have already applied for {job.title} at {job.company.name}."
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg, 'already_applied': True})
        messages.warning(request, msg)
        return redirect('student_applications')

    custom_resume = request.FILES.get('custom_resume')
    use_profile_resume = request.POST.get('use_profile_resume') == '1' or not custom_resume

    # Validate file upload if provided
    if custom_resume:
        ext = custom_resume.name.rsplit('.', 1)[-1].lower() if '.' in custom_resume.name else ''
        if ext not in ('pdf', 'doc', 'docx'):
            msg = "Please upload a valid resume in PDF or DOC/DOCX format."
            if is_ajax:
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('apply_job', job_id=job.id)

        if custom_resume.size > 10 * 1024 * 1024:  # 10MB limit
            msg = "Resume file size exceeds the 10MB limit. Please upload a smaller file."
            if is_ajax:
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('apply_job', job_id=job.id)


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

    # Calculate real match score and breakdown
    match_info = calculate_resume_job_match(
        job,
        resume_file=custom_resume,
        student_profile=profile if use_profile_resume else None
    )

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
        match_percentage=match_info['match_percentage'],
        matched_skills=match_info['matched_skills'],
        missing_skills=match_info['missing_skills'],
        resume_score=match_info['match_percentage'],
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
            'match_percentage': match_info['match_percentage'],
            'matched_skills': match_info['matched_skills'],
            'missing_skills': match_info['missing_skills'],
        })

    messages.success(request, success_msg)
    return redirect('student_applications')


@login_required
def api_resume_match(request):
    """
    Live API endpoint to evaluate resume match against a job.
    Accepts job_id and optional uploaded resume file.
    """
    job_id = request.POST.get('job_id') or request.GET.get('job_id')
    if not job_id:
        return JsonResponse({'success': False, 'message': 'Missing job_id'}, status=400)

    job = get_object_or_404(Job, id=job_id)
    profile = getattr(request.user, 'student_profile', None)
    resume_file = request.FILES.get('resume') or request.FILES.get('custom_resume')

    try:
        match_info = calculate_resume_job_match(
            job,
            resume_file=resume_file,
            student_profile=profile
        )
        return JsonResponse({
            'success': True,
            'job_id': job.id,
            'job_title': job.title,
            'company': job.company.name,
            'match_percentage': match_info['match_percentage'],
            'matched_skills': match_info['matched_skills'],
            'missing_skills': match_info['missing_skills'],
            'recommended_skills': match_info['recommended_skills'],
            'required_skills': job.all_skills_list(),
        })
    except Exception as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=500)


@login_required
@require_POST
def toggle_save_job(request, job_id):
    """
    AJAX endpoint to bookmark/save or remove bookmark for a job
    """
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'success': False, 'message': 'Only students can save jobs.'}, status=403)

    profile = request.user.student_profile
    job = get_object_or_404(Job, id=job_id)

    saved_obj = SavedJob.objects.filter(student=profile, job=job).first()
    if saved_obj:
        saved_obj.delete()
        return JsonResponse({
            'success': True,
            'saved': False,
            'message': f'Removed {job.title} from saved jobs.',
            'job_id': job.id
        })
    else:
        SavedJob.objects.create(student=profile, job=job)
        return JsonResponse({
            'success': True,
            'saved': True,
            'message': f'Saved {job.title} to your bookmarks!',
            'job_id': job.id
        })


@login_required
def saved_jobs_list(request):
    """
    Displays all bookmarked jobs for the logged in student
    """
    profile = getattr(request.user, 'student_profile', None)
    if not profile:
        messages.error(request, "Only registered students can view saved jobs.")
        return redirect('student_dashboard')

    saved_entries = SavedJob.objects.filter(student=profile).select_related('job', 'job__company').prefetch_related('job__required_skills')
    jobs = [entry.job for entry in saved_entries]

    matches = []
    for job in jobs:
        match_info = calculate_resume_job_match(job, student_profile=profile)
        matches.append({
            'job': job,
            'score': match_info['match_percentage'],
            'matched_skills': match_info['matched_skills'],
            'missing_skills': match_info['missing_skills'],
            'recommended_skills': match_info['recommended_skills'],
        })

    applied_ids = set(
        Application.objects.filter(student=profile, job_id__in=[j.id for j in jobs]).values_list('job_id', flat=True)
    )

    context = {
        'job_matches': matches,
        'applied_ids': applied_ids,
        'saved_job_ids': set(j.id for j in jobs),
        'total_saved': len(jobs),
        'student_profile': profile,
    }
    return render(request, 'student/saved_jobs.html', context)


@login_required
def api_company_details(request, company_id):
    """
    Returns full company information and open jobs for modal view
    """
    company = get_object_or_404(Company, id=company_id)
    jobs = company.jobs.filter(is_active=True, is_verified=True).prefetch_related('required_skills')

    jobs_data = []
    for j in jobs:
        jobs_data.append({
            'id': j.id,
            'title': j.title,
            'salary': j.salary or 'Disclosed upon shortlist',
            'location': j.location,
            'work_mode': j.work_mode,
            'job_type': j.job_type,
            'experience_text': j.experience_text or f'{j.experience_required} yrs',
            'qualifications': j.qualifications or j.eligible_degree or 'Engineering degree',
            'deadline': j.application_deadline.strftime('%b %d, %Y') if j.application_deadline else '',
            'skills': j.all_skills_list(),
            'apply_url': f'/jobs/{j.id}/apply/',
            'detail_url': f'/jobs/{j.id}/',
        })

    return JsonResponse({
        'success': True,
        'id': company.id,
        'name': company.name,
        'logo_url': company.get_logo_url,
        'initials': company.initials,
        'brand_color': company.brand_color,
        'industry': company.industry,
        'company_type': company.company_type,
        'tagline': company.tagline,
        'description': company.description,
        'website': company.website,
        'headquarters': company.headquarters or company.locations,
        'locations': company.locations,
        'employee_count': company.employee_count,
        'funding_stage': company.funding_stage,
        'tech_stack': company.tech_stack,
        'required_skills': company.get_required_skills(),
        'jobs': jobs_data,
        'open_positions': len(jobs_data),
    })


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
