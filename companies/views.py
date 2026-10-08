from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from .models import Company, CompanyConnection
from jobs.models import Job, SavedJob
from applications.models import Application


def company_list(request):
    companies = Company.objects.annotate(
        total_jobs=Count('jobs', filter=Q(jobs__is_active=True, jobs__is_verified=True))
    ).order_by('-total_jobs', 'name')

    query = request.GET.get('q', '').strip()
    company_type = request.GET.get('type', '').strip()
    industry = request.GET.get('industry', '').strip()

    if query:
        companies = companies.filter(
            Q(name__icontains=query) |
            Q(industry__icontains=query) |
            Q(tech_stack__icontains=query) |
            Q(locations__icontains=query) |
            Q(headquarters__icontains=query)
        )
    if company_type:
        companies = companies.filter(company_type=company_type)
    if industry:
        companies = companies.filter(industry__icontains=industry)

    connected_ids = set()
    student_profile = None
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        student_profile = request.user.student_profile
        connected_ids = set(
            CompanyConnection.objects.filter(student=student_profile).values_list('company_id', flat=True)
        )

    context = {
        'companies': list(companies),
        'connected_ids': connected_ids,
        'query': query,
        'selected_type': company_type,
        'selected_industry': industry,
        'company_types': ['Enterprise', 'Unicorn', 'Startup', 'Product Lab'],
        'student_profile': student_profile,
    }
    return render(request, 'companies/company_list.html', context)


def company_detail(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    jobs = company.jobs.filter(is_verified=True, is_active=True).prefetch_related('required_skills').order_by('-created_at')

    is_connected = False
    student_profile = None
    applied_ids = set()
    saved_job_ids = set()
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        student_profile = request.user.student_profile
        is_connected = CompanyConnection.objects.filter(student=student_profile, company=company).exists()
        applied_ids = set(Application.objects.filter(student=student_profile, job__in=jobs).values_list('job_id', flat=True))
        saved_job_ids = set(SavedJob.objects.filter(student=student_profile, job__in=jobs).values_list('job_id', flat=True))

    context = {
        'company': company,
        'jobs': jobs,
        'is_connected': is_connected,
        'student_profile': student_profile,
        'applied_ids': applied_ids,
        'saved_job_ids': saved_job_ids,
        'required_skills': company.get_required_skills(),
    }
    return render(request, 'companies/company_detail.html', context)


@login_required
def connect_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1'

    if not hasattr(request.user, 'student_profile'):
        if is_ajax:
            return JsonResponse({'success': False, 'message': 'Only students can connect with companies.'}, status=403)
        messages.error(request, 'Only students can connect with companies.')
        return redirect('company_detail', company_id=company_id)

    profile = request.user.student_profile
    connection, created = CompanyConnection.objects.get_or_create(
        student=profile,
        company=company,
        defaults={
            'preferred_role': request.POST.get('preferred_role', '').strip(),
            'note': request.POST.get('note', '').strip(),
        }
    )

    if not created and request.POST.get('action') == 'disconnect':
        connection.delete()
        if is_ajax:
            return JsonResponse({'success': True, 'connected': False, 'message': f'Disconnected from {company.name}.'})
        messages.info(request, f'Disconnected from {company.name}.')
        return redirect(request.META.get('HTTP_REFERER') or 'company_list')

    if is_ajax:
        return JsonResponse({
            'success': True,
            'connected': True,
            'message': f'Successfully connected with {company.name}! Their founders & hiring team will review your profile.',
            'company_id': company.id,
            'company_name': company.name
        })

    messages.success(request, f'Successfully connected with {company.name}! Their talent team has been notified.')
    return redirect(request.META.get('HTTP_REFERER') or 'company_list')
