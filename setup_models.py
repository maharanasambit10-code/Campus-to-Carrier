import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# 1. Update settings.py
settings_path = BASE_DIR / "campuslink" / "settings.py"
with open(settings_path, "r") as f:
    settings_content = f.read()

apps_to_add = """
    'rest_framework',
    'corsheaders',
    'accounts',
    'students',
    'recruiters',
    'companies',
    'jobs',
    'applications',
    'analytics',
    'ai_engine',
    'interviews',
    'notifications',
    'placements',
"""

if "'accounts'" not in settings_content:
    settings_content = settings_content.replace(
        "'django.contrib.staticfiles',",
        f"'django.contrib.staticfiles',\n{apps_to_add}"
    )
    settings_content += "\nAUTH_USER_MODEL = 'accounts.User'\n"
    
    with open(settings_path, "w") as f:
        f.write(settings_content)


# 2. accounts/models.py
accounts_models = """
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('PLACEMENT_OFFICER', 'Placement Officer'),
        ('RECRUITER', 'Recruiter'),
        ('SUPER_ADMIN', 'Super Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
"""
with open(BASE_DIR / "accounts" / "models.py", "w") as f:
    f.write(accounts_models)

# 3. students/models.py
students_models = """
from django.db import models
from django.conf import settings

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    cgpa = models.FloatField(null=True, blank=True)
    tenth_percentage = models.FloatField(null=True, blank=True)
    twelfth_percentage = models.FloatField(null=True, blank=True)
    active_backlogs = models.IntegerField(default=0)
    skills = models.ManyToManyField(Skill, through='StudentSkill')
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class StudentSkill(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.IntegerField(default=50) # 0-100
"""
with open(BASE_DIR / "students" / "models.py", "w") as f:
    f.write(students_models)

# 4. companies/models.py
companies_models = """
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
"""
with open(BASE_DIR / "companies" / "models.py", "w") as f:
    f.write(companies_models)

# 5. recruiters/models.py
recruiters_models = """
from django.db import models
from django.conf import settings
from companies.models import Company

class RecruiterProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recruiter_profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='recruiters')
    designation = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
"""
with open(BASE_DIR / "recruiters" / "models.py", "w") as f:
    f.write(recruiters_models)

# 6. jobs/models.py
jobs_models = """
from django.db import models
from companies.models import Company
from students.models import Skill

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    description = models.TextField()
    location = models.CharField(max_length=255)
    job_type = models.CharField(max_length=100, default='Full-Time')
    salary = models.CharField(max_length=100, blank=True)
    minimum_cgpa = models.FloatField(default=0.0)
    maximum_backlogs = models.IntegerField(default=0)
    graduation_year = models.IntegerField()
    required_skills = models.ManyToManyField(Skill)
    application_deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
"""
with open(BASE_DIR / "jobs" / "models.py", "w") as f:
    f.write(jobs_models)

# 7. applications/models.py
applications_models = """
from django.db import models
from students.models import StudentProfile
from jobs.models import Job

class Application(models.Model):
    STATUS_CHOICES = (
        ('APPLIED', 'Applied'),
        ('SHORTLISTED', 'Shortlisted'),
        ('ASSESSMENT', 'Assessment'),
        ('INTERVIEW', 'Interview'),
        ('SELECTED', 'Selected'),
        ('REJECTED', 'Rejected'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    resume_score = models.IntegerField(default=0, help_text="AI calculated score")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'job')
"""
with open(BASE_DIR / "applications" / "models.py", "w") as f:
    f.write(applications_models)

# 8. ai_engine/models.py
ai_engine_models = """
from django.db import models
from students.models import StudentProfile

class ResumeAnalysis(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    ats_score = models.IntegerField(default=0)
    extracted_text = models.TextField(blank=True)
    missing_keywords = models.TextField(blank=True)
    improvement_suggestions = models.TextField(blank=True)
    analyzed_at = models.DateTimeField(auto_now=True)

class PlacementPrediction(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    placement_probability = models.FloatField(default=0.0)
    influencing_factors = models.TextField(blank=True)
    predicted_at = models.DateTimeField(auto_now=True)
"""
with open(BASE_DIR / "ai_engine" / "models.py", "w") as f:
    f.write(ai_engine_models)

print("Scaffold complete!")
