import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\bapun\OneDrive\Desktop\BPUT")

# 1. Provide Jobs Views (Job Listing & Application)
jobs_views = """
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Job
from applications.models import Application
from ai_engine.services import match_jobs

@login_required
def job_list(request):
    jobs = Job.objects.all()
    # Mock AI match integration
    if hasattr(request.user, 'student_profile'):
        matches = match_jobs(request.user.student_profile, jobs)
        context = {'job_matches': matches}
    else:
        context = {'jobs': jobs}
    return render(request, 'student/jobs.html', context)

@login_required
def apply_job(request, job_id):
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can apply for jobs.")
        return redirect('student_dashboard')
        
    job = get_object_or_404(Job, id=job_id)
    profile = request.user.student_profile
    
    # Check duplicate
    if Application.objects.filter(student=profile, job=job).exists():
        messages.warning(request, "You have already applied for this job.")
    else:
        Application.objects.create(student=profile, job=job)
        messages.success(request, f"Successfully applied for {job.title} at {job.company.name}!")
        
    return redirect('student_dashboard')
"""
with open(BASE_DIR / "jobs" / "views.py", "w", encoding="utf-8") as f:
    f.write(jobs_views)

# 2. Add Jobs URLs
jobs_urls = """
from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('<int:job_id>/apply/', views.apply_job, name='apply_job'),
]
"""
with open(BASE_DIR / "jobs" / "urls.py", "w", encoding="utf-8") as f:
    f.write(jobs_urls)

# 3. Register Jobs URL in Main URLs
urls_path = BASE_DIR / "campuslink" / "urls.py"
with open(urls_path, "r", encoding="utf-8") as f:
    urls_content = f.read()

if "path('jobs/', include('jobs.urls'))" not in urls_content:
    urls_content = urls_content.replace(
        "path('officer/', include('analytics.urls')),",
        "path('officer/', include('analytics.urls')),\n    path('jobs/', include('jobs.urls')),"
    )
    with open(urls_path, "w", encoding="utf-8") as f:
        f.write(urls_content)


# 4. Student Jobs Template
student_jobs_html = """
{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    <h2 class="fw-bold mb-4">AI Job Marketplace</h2>
    
    {% if messages %}
    <div class="mb-4">
        {% for message in messages %}
        <div class="alert alert-{{ message.tags }}">{{ message }}</div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="row g-4">
        {% for match in job_matches %}
        <div class="col-md-6">
            <div class="card p-4 h-100 shadow-sm border-0 position-relative">
                <span class="position-absolute top-0 end-0 m-3 badge bg-success fs-6">{{ match.score }}% AI MATCH</span>
                <h4 class="fw-bold text-primary">{{ match.job.title }}</h4>
                <h6 class="text-muted fw-bold mb-3"><i class="bi bi-building me-2"></i>{{ match.job.company.name }}</h6>
                
                <div class="mb-3">
                    <span class="badge bg-light text-dark border"><i class="bi bi-geo-alt me-1"></i>{{ match.job.location }}</span>
                    <span class="badge bg-light text-dark border"><i class="bi bi-cash me-1"></i>{{ match.job.salary }}</span>
                </div>
                
                <p class="text-muted small mb-4">{{ match.job.description|truncatewords:20 }}</p>
                
                <div class="mb-3">
                    <h6 class="fw-bold small text-muted">AI Match Analysis:</h6>
                    {% for skill in match.matched_skills %}
                        <span class="badge bg-success bg-opacity-10 text-success border border-success rounded-pill me-1"><i class="bi bi-check-circle me-1"></i>{{ skill|title }}</span>
                    {% endfor %}
                    {% for skill in match.missing_skills %}
                        <span class="badge bg-danger bg-opacity-10 text-danger border border-danger rounded-pill me-1"><i class="bi bi-x-circle me-1"></i>{{ skill|title }}</span>
                    {% endfor %}
                </div>
                
                <div class="mt-auto pt-3 border-top d-flex justify-content-between align-items-center">
                    {% if match.eligible %}
                        <span class="text-success fw-bold small"><i class="bi bi-check-circle-fill me-1"></i>CGPA Eligible</span>
                    {% else %}
                        <span class="text-danger fw-bold small"><i class="bi bi-x-circle-fill me-1"></i>CGPA Not Met</span>
                    {% endif %}
                    
                    <a href="{% url 'apply_job' match.job.id %}" class="btn btn-primary fw-bold px-4">Apply Now</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
"""
(BASE_DIR / "templates" / "student").mkdir(parents=True, exist_ok=True)
with open(BASE_DIR / "templates" / "student" / "jobs.html", "w", encoding="utf-8") as f:
    f.write(student_jobs_html)

# 5. Fix Student Dashboard Links
dashboard_path = BASE_DIR / "templates" / "student" / "dashboard.html"
with open(dashboard_path, "r", encoding="utf-8") as f:
    dashboard_content = f.read()

dashboard_content = dashboard_content.replace(
    '<li class="nav-item"><a class="nav-link text-muted" href="#"><i class="bi bi-search me-2"></i> Find Jobs</a></li>',
    '<li class="nav-item"><a class="nav-link text-muted" href="/jobs/"><i class="bi bi-search me-2"></i> Find Jobs</a></li>'
)
with open(dashboard_path, "w", encoding="utf-8") as f:
    f.write(dashboard_content)

print("Final Rapid Build setup script generated successfully!")
