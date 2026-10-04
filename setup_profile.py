import os
from pathlib import Path

BASE_DIR = Path(r"C:\Users\bapun\OneDrive\Desktop\BPUT")

# 1. Update Models
models_path = BASE_DIR / "students" / "models.py"
with open(models_path, "r", encoding="utf-8") as f:
    models_content = f.read()

if "class Project" not in models_content:
    new_models = """
class Project(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    description = models.TextField()
    technologies = models.CharField(max_length=200)
    github_url = models.URLField(blank=True)
    
class Internship(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='internships')
    company = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    description = models.TextField()

class Certification(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
"""
    # Also add profile_photo to StudentProfile
    if "profile_photo =" not in models_content:
        models_content = models_content.replace(
            "active_backlogs = models.IntegerField(default=0)",
            "active_backlogs = models.IntegerField(default=0)\n    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)"
        )
    
    with open(models_path, "w", encoding="utf-8") as f:
        f.write(models_content + "\n" + new_models)


# 2. Update Views
views_path = BASE_DIR / "students" / "views.py"
with open(views_path, "r", encoding="utf-8") as f:
    views_content = f.read()

if "def student_profile" not in views_content:
    views_addition = """
@login_required
def student_profile(request):
    try:
        profile = request.user.student_profile
    except:
        profile = None
    
    if request.method == 'POST' and profile:
        profile.phone = request.POST.get('phone', profile.phone)
        profile.department = request.POST.get('department', profile.department)
        profile.github = request.POST.get('github', profile.github)
        profile.linkedin = request.POST.get('linkedin', profile.linkedin)
        if 'profile_photo' in request.FILES:
            profile.profile_photo = request.FILES['profile_photo']
        if 'resume' in request.FILES:
            profile.resume = request.FILES['resume']
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('student_profile')
        
    context = {'profile': profile}
    return render(request, 'student/profile.html', context)
"""
    views_content = views_content.replace("from django.contrib.auth.decorators import login_required", "from django.contrib.auth.decorators import login_required\nfrom django.contrib import messages\nfrom django.shortcuts import redirect")
    with open(views_path, "a", encoding="utf-8") as f:
        f.write("\n" + views_addition)


# 3. Update URLs
urls_path = BASE_DIR / "students" / "urls.py"
with open(urls_path, "r", encoding="utf-8") as f:
    urls_content = f.read()

if "path('profile/', views.student_profile" not in urls_content:
    urls_content = urls_content.replace(
        "path('dashboard/', views.student_dashboard, name='student_dashboard'),",
        "path('dashboard/', views.student_dashboard, name='student_dashboard'),\n    path('profile/', views.student_profile, name='student_profile'),"
    )
    with open(urls_path, "w", encoding="utf-8") as f:
        f.write(urls_content)


# 4. Profile Template
profile_html = """
{% extends 'base.html' %}
{% block content %}
<div class="container py-5">
    {% if messages %}
    <div class="mb-4">
        {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="row">
        <!-- Left Sidebar: Profile Card -->
        <div class="col-md-4 mb-4">
            <div class="card p-4 text-center border-0 shadow-sm h-100">
                <div class="mb-4">
                    {% if profile.profile_photo %}
                        <img src="{{ profile.profile_photo.url }}" class="rounded-circle img-thumbnail" style="width:150px; height:150px; object-fit:cover;">
                    {% else %}
                        <img src="https://ui-avatars.com/api/?name={{ request.user.username }}&background=4f46e5&color=fff&size=150" class="rounded-circle img-thumbnail">
                    {% endif %}
                </div>
                <h3 class="fw-bold">{{ profile.user.get_full_name|default:profile.user.username }}</h3>
                <p class="text-muted">{{ profile.department|default:"Department not set" }}</p>
                <div class="d-flex justify-content-center gap-2 mb-4">
                    {% if profile.linkedin %}<a href="{{ profile.linkedin }}" class="btn btn-outline-primary btn-sm"><i class="bi bi-linkedin"></i></a>{% endif %}
                    {% if profile.github %}<a href="{{ profile.github }}" class="btn btn-outline-dark btn-sm"><i class="bi bi-github"></i></a>{% endif %}
                </div>
                
                <h6 class="fw-bold text-start mb-2">Profile Completion</h6>
                <div class="progress mb-2" style="height: 10px;">
                    <div class="progress-bar bg-success" role="progressbar" style="width: 82%"></div>
                </div>
                <p class="small text-muted text-start">82% Complete</p>
            </div>
        </div>

        <!-- Right Content: Edit Form & Details -->
        <div class="col-md-8">
            <div class="card p-4 border-0 shadow-sm mb-4">
                <h4 class="fw-bold mb-4 border-bottom pb-2">Personal Information</h4>
                <form method="post" enctype="multipart/form-data">
                    {% csrf_token %}
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label text-muted small fw-bold">Phone Number</label>
                            <input type="text" name="phone" class="form-control" value="{{ profile.phone|default:'' }}">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label text-muted small fw-bold">Department</label>
                            <input type="text" name="department" class="form-control" value="{{ profile.department|default:'' }}">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label text-muted small fw-bold">LinkedIn URL</label>
                            <input type="url" name="linkedin" class="form-control" value="{{ profile.linkedin|default:'' }}">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label text-muted small fw-bold">GitHub URL</label>
                            <input type="url" name="github" class="form-control" value="{{ profile.github|default:'' }}">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label text-muted small fw-bold">Profile Photo</label>
                            <input type="file" name="profile_photo" class="form-control" accept="image/jpeg, image/png">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label text-muted small fw-bold">Resume (PDF)</label>
                            <input type="file" name="resume" class="form-control" accept="application/pdf">
                        </div>
                    </div>
                    <div class="mt-4 text-end">
                        <button type="submit" class="btn btn-primary fw-bold px-4"><i class="bi bi-save me-2"></i>Save Changes</button>
                    </div>
                </form>
            </div>
            
            <div class="card p-4 border-0 shadow-sm">
                <h4 class="fw-bold mb-4 border-bottom pb-2">Technical Skills</h4>
                <div class="d-flex flex-wrap gap-2">
                    {% for sskill in profile.studentskill_set.all %}
                        <span class="badge badge-soft-primary fs-6">{{ sskill.skill.name }} <i class="bi bi-x ms-1" style="cursor:pointer;"></i></span>
                    {% empty %}
                        <p class="text-muted">No skills added yet.</p>
                    {% endfor %}
                    <button class="btn btn-sm btn-outline-primary rounded-pill"><i class="bi bi-plus"></i> Add Skill</button>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""
with open(BASE_DIR / "templates" / "student" / "profile.html", "w", encoding="utf-8") as f:
    f.write(profile_html)

# 5. Fix Navbar Dropdown Links
base_path = BASE_DIR / "templates" / "base.html"
with open(base_path, "r", encoding="utf-8") as f:
    base_content = f.read()

base_content = base_content.replace(
    '<li><a class="dropdown-item" href="#">Profile</a></li>',
    """
    <li><a class="dropdown-item" href="/dashboard/">Dashboard</a></li>
    <li><a class="dropdown-item" href="{% if request.user.role == 'STUDENT' %}/student/profile/{% else %}#{% endif %}">Profile</a></li>
    """
)
with open(base_path, "w", encoding="utf-8") as f:
    f.write(base_content)

print("Profile logic setup successfully.")
