import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\bapun\OneDrive\Desktop\BPUT")

# 1. Update Core URL Routing
urls_code = """
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from accounts.views import CustomLoginView, dashboard_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
    path('student/', include('students.urls')),
    path('officer/', include('analytics.urls')),
]
"""
with open(BASE_DIR / "campuslink" / "urls.py", "w", encoding="utf-8") as f:
    f.write(urls_code)

# 2. Accounts Views (Auth & Redirect)
accounts_views = """
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        user = self.request.user
        if user.role == 'STUDENT':
            return reverse('student_dashboard')
        elif user.role == 'PLACEMENT_OFFICER':
            return reverse('officer_dashboard')
        elif user.role == 'RECRUITER':
            return reverse('recruiter_dashboard')
        return super().get_success_url()

def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role == 'STUDENT':
        return redirect('student_dashboard')
    elif request.user.role == 'PLACEMENT_OFFICER':
        return redirect('officer_dashboard')
    return redirect('home')
"""
with open(BASE_DIR / "accounts" / "views.py", "w", encoding="utf-8") as f:
    f.write(accounts_views)

# 3. Students Views & URLs
student_urls = """
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
]
"""
with open(BASE_DIR / "students" / "urls.py", "w", encoding="utf-8") as f:
    f.write(student_urls)

student_views = """
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from jobs.models import Job
from applications.models import Application
from .models import StudentProfile

@login_required
def student_dashboard(request):
    try:
        profile = request.user.student_profile
    except:
        profile = None
        
    recommended_jobs = Job.objects.all()[:4]
    applications = Application.objects.filter(student=profile) if profile else []
    
    context = {
        'readiness': 87,
        'resume_score': 84,
        'recommended_jobs': len(recommended_jobs),
        'applications_count': len(applications),
        'top_jobs': recommended_jobs,
        'recent_apps': applications,
    }
    return render(request, 'student/dashboard.html', context)
"""
with open(BASE_DIR / "students" / "views.py", "w", encoding="utf-8") as f:
    f.write(student_views)

# 4. Officer Views & URLs
analytics_urls = """
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.officer_dashboard, name='officer_dashboard'),
]
"""
with open(BASE_DIR / "analytics" / "urls.py", "w", encoding="utf-8") as f:
    f.write(analytics_urls)

analytics_views = """
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from students.models import StudentProfile
from jobs.models import Job
from applications.models import Application

@login_required
def officer_dashboard(request):
    context = {
        'total_students': StudentProfile.objects.count(),
        'eligible_students': StudentProfile.objects.filter(cgpa__gte=7.0).count(),
        'active_jobs': Job.objects.count(),
        'total_applications': Application.objects.count(),
        'placed_students': Application.objects.filter(status='SELECTED').count(),
    }
    return render(request, 'officer/dashboard.html', context)
"""
with open(BASE_DIR / "analytics" / "views.py", "w", encoding="utf-8") as f:
    f.write(analytics_views)

# 5. Simple Login Template
login_html = """
{% extends 'base.html' %}
{% block content %}
<div class="container my-5">
    <div class="row justify-content-center">
        <div class="col-md-5">
            <div class="card p-4 shadow-sm">
                <h3 class="fw-bold mb-4 text-center">Login to CAMPUSLINK</h3>
                <form method="post">
                    {% csrf_token %}
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" name="username" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" name="password" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 fw-bold">Login</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(BASE_DIR / "templates" / "login.html", "w", encoding="utf-8") as f:
    f.write(login_html)

print("Phase 4 URL & View wiring complete!")
