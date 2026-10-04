import os
from pathlib import Path
import json

BASE_DIR = Path(r"C:\Users\bapun\OneDrive\Desktop\BPUT")
STATIC_DIR = BASE_DIR / "static"
JS_DIR = STATIC_DIR / "js"
CSS_DIR = STATIC_DIR / "css"

for d in [STATIC_DIR, JS_DIR, CSS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 1. Update settings.py for Static Files
settings_path = BASE_DIR / "campuslink" / "settings.py"
with open(settings_path, "r", encoding="utf-8") as f:
    settings_content = f.read()

if "STATICFILES_DIRS" not in settings_content:
    settings_content += "\nSTATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]\n"
    with open(settings_path, "w", encoding="utf-8") as f:
        f.write(settings_content)

# 2. Add some premium CSS
css_content = """
:root { --primary-color: #0d6efd; --secondary-color: #6c757d; }
body { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
.card { border: none; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s ease, box-shadow 0.2s ease; }
.card:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
.sidebar { background: white; min-height: 100vh; box-shadow: 2px 0 5px rgba(0,0,0,0.05); }
.nav-link { font-weight: 500; padding: 12px 20px; color: var(--secondary-color); border-radius: 8px; margin-bottom: 5px; }
.nav-link:hover, .nav-link.active { background-color: #e9ecef; color: var(--primary-color); }
"""
with open(CSS_DIR / "style.css", "w", encoding="utf-8") as f:
    f.write(css_content)

# 3. Create Recruiter Dashboard View & Template
recruiter_views = """
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from jobs.models import Job
from applications.models import Application

@login_required
def recruiter_dashboard(request):
    try:
        profile = request.user.recruiter_profile
        company = profile.company
    except:
        company = None
        
    jobs = Job.objects.filter(company=company) if company else []
    applications = Application.objects.filter(job__company=company) if company else []
    
    context = {
        'active_jobs': len(jobs),
        'total_applicants': len(applications),
        'shortlisted': len([a for a in applications if a.status == 'SHORTLISTED']),
        'interviews': len([a for a in applications if a.status == 'INTERVIEW']),
        'recent_applicants': applications[:5],
    }
    return render(request, 'recruiter/dashboard.html', context)
"""
with open(BASE_DIR / "recruiters" / "views.py", "w", encoding="utf-8") as f:
    f.write(recruiter_views)

recruiter_urls = """
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
]
"""
with open(BASE_DIR / "recruiters" / "urls.py", "w", encoding="utf-8") as f:
    f.write(recruiter_urls)

recruiter_dashboard_html = """
{% extends 'base.html' %}
{% block content %}
<div class="container-fluid">
    <div class="row">
        <!-- Sidebar -->
        <div class="col-md-2 sidebar py-4">
            <h5 class="fw-bold px-3 mb-4 text-primary">Recruiter Panel</h5>
            <ul class="nav flex-column gap-2">
                <li class="nav-item"><a class="nav-link active fw-bold text-dark" href="#"><i class="bi bi-grid me-2"></i> Dashboard</a></li>
                <li class="nav-item"><a class="nav-link text-muted" href="#"><i class="bi bi-briefcase me-2"></i> Active Jobs</a></li>
                <li class="nav-item"><a class="nav-link text-muted" href="#"><i class="bi bi-people me-2"></i> Applicants</a></li>
                <li class="nav-item"><a class="nav-link text-muted" href="#"><i class="bi bi-robot me-2"></i> AI Shortlist</a></li>
            </ul>
        </div>
        <!-- Main Content -->
        <div class="col-md-10 p-5">
            <h2 class="mb-4">Recruiter Dashboard</h2>
            <div class="row g-4 mb-5">
                <div class="col-md-3">
                    <div class="card p-4 border-start border-primary border-4">
                        <h6 class="text-muted fw-bold">Active Jobs</h6>
                        <h2 class="fw-bold">{{ active_jobs }}</h2>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card p-4 border-start border-success border-4">
                        <h6 class="text-muted fw-bold">Applicants</h6>
                        <h2 class="fw-bold text-success">{{ total_applicants }}</h2>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card p-4 border-start border-warning border-4">
                        <h6 class="text-muted fw-bold">Shortlisted</h6>
                        <h2 class="fw-bold">{{ shortlisted }}</h2>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card p-4 border-start border-info border-4">
                        <h6 class="text-muted fw-bold">Interviews</h6>
                        <h2 class="fw-bold text-info">{{ interviews }}</h2>
                    </div>
                </div>
            </div>
            
            <h4 class="fw-bold mb-3">Recent Applicants (AI Ranked)</h4>
            <div class="card p-4">
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>Candidate</th>
                            <th>CGPA</th>
                            <th>AI Match Score</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for app in recent_applicants %}
                        <tr>
                            <td>
                                <div class="fw-bold">{{ app.student.user.username }}</div>
                                <div class="text-muted small">{{ app.job.title }}</div>
                            </td>
                            <td>{{ app.student.cgpa }}</td>
                            <td>
                                <div class="progress" style="height: 10px; width: 100px;">
                                    <div class="progress-bar bg-success" role="progressbar" style="width: 92%"></div>
                                </div>
                                <span class="small text-success fw-bold">92%</span>
                            </td>
                            <td><span class="badge bg-primary">{{ app.status }}</span></td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary">View</button>
                                <button class="btn btn-sm btn-success">Shortlist</button>
                            </td>
                        </tr>
                        {% empty %}
                        <tr><td colspan="5" class="text-center text-muted">No applicants found.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(BASE_DIR / "templates" / "recruiter" / "dashboard.html", "w", encoding="utf-8") as f:
    f.write(recruiter_dashboard_html)

# 4. Update Main URL routes
urls_path = BASE_DIR / "campuslink" / "urls.py"
with open(urls_path, "r", encoding="utf-8") as f:
    urls_content = f.read()

if "path('recruiter/', include('recruiters.urls'))" not in urls_content:
    urls_content = urls_content.replace(
        "path('officer/', include('analytics.urls')),",
        "path('officer/', include('analytics.urls')),\n    path('recruiter/', include('recruiters.urls')),"
    )
    with open(urls_path, "w", encoding="utf-8") as f:
        f.write(urls_content)

print("Phase 5 Scaffolding Complete!")
