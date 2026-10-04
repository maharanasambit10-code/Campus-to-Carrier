
import re

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from students.models import StudentProfile
from jobs.models import Job
from applications.models import Application
from companies.models import Company
from notifications.models import Notification
from accounts.decorators import role_required


def _package_value(salary):
    """Extract an annual package value in LPA from common salary labels."""
    value = re.search(r'(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lakh)', salary or '', re.IGNORECASE)
    return float(value.group(1)) if value else None

@role_required('PLACEMENT_OFFICER', 'SUPER_ADMIN')
def officer_dashboard(request):
    total_students = StudentProfile.objects.count()
    placed_students = Application.objects.filter(status='SELECTED').values('student_id').distinct().count()
    eligible_students = StudentProfile.objects.filter(cgpa__gte=7.0, active_backlogs=0).count()
    placement_rate = round((placed_students / total_students) * 100) if total_students else 0
    selected_jobs = Job.objects.filter(applications__status='SELECTED').distinct()
    package_values = [value for value in (_package_value(job.salary) for job in selected_jobs) if value is not None]
    average_package = round(sum(package_values) / len(package_values), 1) if package_values else 0
    highest_package = max(package_values, default=0)
    context = {
        'total_students': total_students,
        'eligible_students': eligible_students,
        'active_jobs': Job.objects.count(),
        'total_applications': Application.objects.count(),
        'placed_students': placed_students,
        'placement_rate': placement_rate,
        'average_package': average_package,
        'highest_package': highest_package,
        'pending_companies': Company.objects.filter(verification_status='PENDING').order_by('-created_at')[:8],
        'recent_applications': Application.objects.select_related('student__user', 'job__company').order_by('-updated_at')[:8],
        'notifications': Notification.objects.filter(user=request.user, is_read=False)[:5],
    }
    return render(request, 'officer/dashboard.html', context)


@role_required('PLACEMENT_OFFICER', 'SUPER_ADMIN')
def verify_company(request, company_id):
    if request.method != 'POST':
        return redirect('officer_dashboard')
    company = get_object_or_404(Company, id=company_id)
    status = request.POST.get('status')
    if status in {'VERIFIED', 'REJECTED', 'PENDING'}:
        company.verification_status = status
        company.save(update_fields=['verification_status', 'updated_at'])
        messages.success(request, f'{company.name} is now marked {company.get_verification_status_display()}.')
    return redirect('officer_dashboard')
