
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from jobs.models import Job
from applications.models import Application
from .forms import AchievementForm, CertificationForm, InternshipForm, ProjectForm, StudentProfileForm
from .models import Achievement, Certification, Internship, Project, Skill, StudentProfile, StudentSkill
from ai_engine.services import analyze_resume_for_student, calculate_career_readiness, match_jobs
from ai_engine.models import ResumeAnalysis
from accounts.decorators import role_required
from accounts.models import Membership


def _get_student_profile(user):
    profile, _ = StudentProfile.objects.get_or_create(user=user)
    return profile

@role_required('STUDENT')
def student_dashboard(request):
    profile = _get_student_profile(request.user)
    applications = Application.objects.filter(student=profile).select_related('job', 'job__company')
    all_jobs = Job.objects.select_related('company').prefetch_related('required_skills', 'preferred_skills')
    career_matches = match_jobs(profile, all_jobs)
    recommended_jobs = [match['job'] for match in career_matches[:4]]
    shortlisted_statuses = {'SHORTLISTED', 'INTERVIEW', 'SELECTED'}
    selected_jobs = applications.filter(status='SELECTED')
    resume_analysis = ResumeAnalysis.objects.filter(student=profile).first()
    missing_profile_items = [label for key, label in (
        ('basic_information', 'Basic information'), ('education', 'Education'),
        ('skills', 'Skills'), ('projects', 'Projects'), ('resume', 'Resume'),
        ('professional_links', 'Professional links'),
    ) if not profile.profile_strength.get(key)]
    context = {
        'profile': profile,
        'profile_completion': profile.completion_percentage,
        'applications_count': applications.count(),
        'shortlisted_count': applications.filter(status__in=shortlisted_statuses).count(),
        'selected_count': selected_jobs.count(),
        'recommended_count': len(recommended_jobs),
        'top_jobs': recommended_jobs,
        'recent_apps': applications.order_by('-created_at')[:5],
        'career_match_count': sum(match['status'] == 'ELIGIBLE' for match in career_matches),
        'top_career_match': career_matches[0] if career_matches else None,
        'resume_analysis': resume_analysis,
        'missing_profile_items': missing_profile_items,
        'membership': Membership.objects.get_or_create(user=request.user)[0],
        'current_server_time': timezone.now(),
    }
    return render(request, 'student/dashboard.html', context)


@role_required('STUDENT')
def student_applications(request):
    profile = _get_student_profile(request.user)
    applications = Application.objects.filter(student=profile).select_related('job', 'job__company').order_by('-created_at')
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    if query:
        applications = applications.filter(Q(job__title__icontains=query) | Q(job__company__name__icontains=query))
    if status:
        applications = applications.filter(status=status)
    context = {
        'applications': applications,
        'query': query,
        'selected_status': status,
        'status_choices': Application.STATUS_CHOICES,
        'total_count': applications.count(),
        'applied_count': applications.filter(status='APPLIED').count(),
        'shortlisted_count': applications.filter(status='SHORTLISTED').count(),
        'interview_count': applications.filter(status__in=['ASSESSMENT', 'INTERVIEW']).count(),
        'selected_count': applications.filter(status='SELECTED').count(),
        'profile_completion': profile.completion_percentage,
    }
    return render(request, 'student/applications.html', context)


@role_required('STUDENT')
def student_profile(request):
    profile = _get_student_profile(request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            if request.FILES.get('resume'):
                membership = getattr(request.user, 'membership', None)
                is_pro = bool(membership and membership.is_active)
                if is_pro:
                    analysis = analyze_resume_for_student(profile, request.FILES['resume'])
                    if analysis.parse_error:
                        messages.warning(request, analysis.parse_error)
                    else:
                        messages.success(request, 'Resume analyzed. Your career matches are ready.')
                else:
                    messages.info(request, 'Resume uploaded. Upgrade to CampusLink PRO (₹1) and submit payment screenshot to activate AI ATS analysis and role matching.')
            messages.success(request, 'Profile updated successfully.')
            return redirect('student_profile')
    else:
        form = StudentProfileForm(instance=profile)

    completion_fields = [
        profile.profile_photo, profile.phone, profile.department, profile.college,
        profile.graduation_year, profile.cgpa, profile.tenth_percentage,
        profile.twelfth_percentage, profile.location, profile.about_me,
        profile.career_objective, profile.studentskill_set.exists(), profile.github,
        profile.linkedin, profile.portfolio, profile.resume,
    ]
    completion = round(sum(bool(field) for field in completion_fields) / len(completion_fields) * 100)

    context = {
        'profile': profile,
        'profile_form': form,
        'project_form': ProjectForm(),
        'available_skills': Skill.objects.order_by('name'),
        'student_skills': profile.studentskill_set.select_related('skill'),
        'projects': profile.projects.all(),
        'profile_completion': completion,
        'profile_strength': profile.profile_strength,
        'certification_form': CertificationForm(),
        'internship_form': InternshipForm(),
        'achievement_form': AchievementForm(),
        'certifications': profile.certifications.all(),
        'internships': profile.internships.all(),
        'achievements': profile.achievements.all(),
        'profile_stats': [
            ('bi-lightning-charge', 'Readiness', f'{calculate_career_readiness(profile)}/100', '#career-insights'),
            ('bi-code-square', 'Skills', profile.studentskill_set.count(), '#skills'),
            ('bi-kanban', 'Projects', profile.projects.count(), '#projects'),
            ('bi-award', 'Credentials', profile.certifications.count(), '#certifications'),
            ('bi-briefcase', 'Experience', profile.internships.count(), '#experience'),
            ('bi-trophy', 'Achievements', profile.achievements.count(), '#achievements'),
        ],
        'career_readiness': calculate_career_readiness(profile),
        'career_matches': match_jobs(profile, Job.objects.select_related('company').prefetch_related('required_skills')[:6])[:3],
        'resume_analysis': ResumeAnalysis.objects.filter(student=profile).first(),
    }
    return render(request, 'student/profile.html', context)


@role_required('STUDENT')
def career_match(request):
    profile = _get_student_profile(request.user)
    membership = getattr(request.user, 'membership', None)
    is_pro = bool(membership and membership.is_active)

    if request.method == 'POST' and request.FILES.get('resume'):
        if not is_pro:
            messages.error(
                request,
                'AI Resume Analyzer is a PRO premium feature. Please upgrade to PRO (₹1) and upload your payment screenshot to unlock full AI analysis.'
            )
            return redirect('pro_checkout')

        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                analysis = analyze_resume_for_student(profile, request.FILES['resume'])
                if analysis.parse_error:
                    messages.warning(request, analysis.parse_error)
                else:
                    messages.success(request, 'Resume analyzed successfully.')
            except Exception as exc:
                messages.error(request, f'Resume analysis failed: {exc}')
            return redirect('career_match')
    jobs = Job.objects.select_related('company').prefetch_related('required_skills', 'preferred_skills').order_by('-created_at')
    matches = match_jobs(profile, jobs)
    status_filter = request.GET.get('status', '').strip().upper()
    if status_filter in {'ELIGIBLE', 'PARTIAL MATCH', 'NOT CURRENTLY ELIGIBLE'}:
        matches = [match for match in matches if match['status'] == status_filter]
    query = request.GET.get('q', '').strip().lower()
    location = request.GET.get('location', '').strip().lower()
    skill = request.GET.get('skill', '').strip().lower()
    try:
        minimum_score = int(request.GET.get('min_score', '0'))
    except ValueError:
        minimum_score = 0
    if query:
        matches = [match for match in matches if query in match['job'].title.lower() or query in match['job'].company.name.lower()]
    if location:
        matches = [match for match in matches if location in match['job'].location.lower()]
    if skill:
        matches = [match for match in matches if skill in {item.lower() for item in match['matched_skills'] + match['missing_skills']}]
    matches = [match for match in matches if match['score'] >= minimum_score]
    analysis = ResumeAnalysis.objects.filter(student=profile).first()
    context = {
        'profile': profile,
        'analysis': analysis,
        'analysis_skills_count': len(analysis.skills) if analysis and analysis.skills else 0,
        'analysis_degree': analysis.degree if analysis and analysis.degree else '',
        'analysis_parse_error': analysis.parse_error if analysis else '',
        'matches': matches,
        'eligible_matches': [match for match in matches if match['status'] == 'ELIGIBLE'],
        'partial_matches': [match for match in matches if match['status'] == 'PARTIAL MATCH'],
        'ineligible_matches': [match for match in matches if match['status'] == 'NOT CURRENTLY ELIGIBLE'],
        'status_filter': status_filter,
        'query': query,
        'location': location,
        'skill_filter': skill,
        'minimum_score': minimum_score,
        'student_skills': sorted(item.skill.name for item in profile.studentskill_set.select_related('skill')),
        'skill_gap_matches': [match for match in matches if match['status'] in {'PARTIAL MATCH', 'NOT CURRENTLY ELIGIBLE'}],
        'upload_form': StudentProfileForm(instance=profile),
        'is_pro': is_pro,
        'membership': membership,
    }
    return render(request, 'student/career_match.html', context)


@role_required('STUDENT')
def resume_download(request):
    profile = _get_student_profile(request.user)
    if not profile.resume:
        raise Http404('Resume not found.')
    return FileResponse(profile.resume.open('rb'), as_attachment=False, filename=profile.resume.name.rsplit('/', 1)[-1])


@role_required('STUDENT')
def add_skill(request):
    if request.method != 'POST':
        return redirect('student_profile')

    profile = _get_student_profile(request.user)

    skill_name = request.POST.get('skill_name', '').strip()
    existing_skill_id = request.POST.get('existing_skill', '').strip()
    proficiency = request.POST.get('proficiency', '50')

    if existing_skill_id:
        skill = Skill.objects.filter(pk=existing_skill_id).first()
    elif skill_name:
        skill, _ = Skill.objects.get_or_create(name=skill_name.title())
    else:
        skill = None

    if not skill:
        messages.error(request, 'Choose an existing skill or enter a new one.')
        return redirect('student_profile')

    try:
        proficiency = max(0, min(100, int(proficiency)))
    except ValueError:
        proficiency = 50

    if StudentSkill.objects.filter(student=profile, skill=skill).exists():
        messages.warning(request, f'{skill.name} is already in your skill list.')
    else:
        StudentSkill.objects.create(student=profile, skill=skill, proficiency=proficiency)
        messages.success(request, f'{skill.name} added to your skills.')

    return redirect('student_profile')


@role_required('STUDENT')
def update_skill(request, skill_id):
    if request.method != 'POST':
        return redirect('student_profile')

    profile = _get_student_profile(request.user)
    student_skill = get_object_or_404(StudentSkill, pk=skill_id, student=profile)
    try:
        proficiency = int(request.POST.get('proficiency', student_skill.proficiency))
    except (TypeError, ValueError):
        proficiency = student_skill.proficiency
    student_skill.proficiency = max(0, min(100, proficiency))
    student_skill.save(update_fields=['proficiency'])
    messages.success(request, f'{student_skill.skill.name} proficiency updated.')
    return redirect('student_profile')


@role_required('STUDENT')
def delete_skill(request, skill_id):
    if request.method == 'POST':
        profile = _get_student_profile(request.user)
        student_skill = get_object_or_404(StudentSkill, pk=skill_id, student=profile)
        skill_name = student_skill.skill.name
        student_skill.delete()
        messages.success(request, f'{skill_name} removed from your skills.')
    return redirect('student_profile')


@role_required('STUDENT')
def save_project(request):
    profile = _get_student_profile(request.user)
    if request.method != 'POST':
        return redirect('student_profile')

    form = ProjectForm(request.POST, request.FILES)
    if form.is_valid():
        project = form.save(commit=False)
        project.student = profile
        project.save()
        messages.success(request, 'Project added to your profile.')
    else:
        messages.error(request, 'Please correct the project form and try again.')
    return redirect('student_profile')


@role_required('STUDENT')
def edit_project(request, project_id):
    profile = _get_student_profile(request.user)
    project = get_object_or_404(Project, pk=project_id, student=profile)
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('student_profile')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'student/project_form.html', {'form': form, 'project': project})


@role_required('STUDENT')
def delete_project(request, project_id):
    if request.method == 'POST':
        profile = _get_student_profile(request.user)
        project = get_object_or_404(Project, pk=project_id, student=profile)
        project.delete()
        messages.success(request, 'Project removed from your profile.')
    return redirect('student_profile')


@role_required('STUDENT')
def recruiter_preview(request):
    profile = _get_student_profile(request.user)
    return render(request, 'student/recruiter_preview.html', {
        'profile': profile,
        'student_skills': profile.studentskill_set.select_related('skill'),
        'projects': profile.projects.all(),
        'certifications': profile.certifications.all(),
        'internships': profile.internships.all(),
        'achievements': profile.achievements.all(),
        'career_readiness': calculate_career_readiness(profile),
    })


def _record_form(request, form_class, template_title, instance=None):
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.student = _get_student_profile(request.user)
        record.save()
        messages.success(request, f'{template_title} saved successfully.')
        return redirect('student_profile')
    return render(request, 'student/record_form.html', {'form': form, 'title': template_title})


@role_required('STUDENT')
def save_certification(request):
    return _record_form(request, CertificationForm, 'Certification')


@role_required('STUDENT')
def edit_certification(request, certification_id):
    record = get_object_or_404(Certification, id=certification_id, student=_get_student_profile(request.user))
    return _record_form(request, CertificationForm, 'Certification', record)


@role_required('STUDENT')
def delete_certification(request, certification_id):
    if request.method == 'POST':
        get_object_or_404(Certification, id=certification_id, student=_get_student_profile(request.user)).delete()
        messages.success(request, 'Certification removed.')
    return redirect('student_profile')


@role_required('STUDENT')
def save_internship(request):
    return _record_form(request, InternshipForm, 'Experience')


@role_required('STUDENT')
def edit_internship(request, internship_id):
    record = get_object_or_404(Internship, id=internship_id, student=_get_student_profile(request.user))
    return _record_form(request, InternshipForm, 'Experience', record)


@role_required('STUDENT')
def delete_internship(request, internship_id):
    if request.method == 'POST':
        get_object_or_404(Internship, id=internship_id, student=_get_student_profile(request.user)).delete()
        messages.success(request, 'Experience removed.')
    return redirect('student_profile')


@role_required('STUDENT')
def save_achievement(request):
    return _record_form(request, AchievementForm, 'Achievement')


@role_required('STUDENT')
def edit_achievement(request, achievement_id):
    record = get_object_or_404(Achievement, id=achievement_id, student=_get_student_profile(request.user))
    return _record_form(request, AchievementForm, 'Achievement', record)


@role_required('STUDENT')
def delete_achievement(request, achievement_id):
    if request.method == 'POST':
        get_object_or_404(Achievement, id=achievement_id, student=_get_student_profile(request.user)).delete()
        messages.success(request, 'Achievement removed.')
    return redirect('student_profile')
