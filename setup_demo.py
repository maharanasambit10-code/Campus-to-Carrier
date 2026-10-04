import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

cmd_dir = BASE_DIR / "jobs" / "management" / "commands"
cmd_dir.mkdir(parents=True, exist_ok=True)

seed_demo_code = """
from django.core.management.base import BaseCommand
from accounts.models import User
from students.models import Skill, StudentProfile, StudentSkill
from companies.models import Company
from recruiters.models import RecruiterProfile
from jobs.models import Job

class Command(BaseCommand):
    help = 'Seeds the database with demo data for CAMPUSLINK'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database with demo data...')
        
        # Skills
        python, _ = Skill.objects.get_or_create(name="Python")
        django, _ = Skill.objects.get_or_create(name="Django")
        react, _ = Skill.objects.get_or_create(name="React")
        
        # Company
        company, _ = Company.objects.get_or_create(name="Tech Innovations Inc.", description="A leading tech company.", website="https://techinnovations.example.com")
        
        # Users
        student_user, _ = User.objects.get_or_create(username="student1", email="student1@example.com", role="STUDENT")
        student_user.set_password("password123")
        student_user.save()

        bapuni_user, _ = User.objects.get_or_create(username="bapuni_123", email="bapuni_123@example.com", role="STUDENT")
        bapuni_user.set_password("Bapuni@123")
        bapuni_user.save()
        
        recruiter_user, _ = User.objects.get_or_create(username="recruiter1", email="recruiter@example.com", role="RECRUITER")
        recruiter_user.set_password("password123")
        recruiter_user.save()

        # Profiles
        student_profile, _ = StudentProfile.objects.get_or_create(user=student_user, cgpa=8.5, graduation_year=2025, department="Computer Science")
        StudentSkill.objects.get_or_create(student=student_profile, skill=python, proficiency=90)
        StudentSkill.objects.get_or_create(student=student_profile, skill=django, proficiency=85)
        
        RecruiterProfile.objects.get_or_create(user=recruiter_user, company=company, designation="Senior Technical Recruiter")
        
        # Jobs
        from django.utils import timezone
        import datetime
        job, _ = Job.objects.get_or_create(
            title="Python Backend Developer",
            company=company,
            description="We are looking for a skilled Django developer.",
            location="Remote",
            salary="$80,000",
            minimum_cgpa=7.0,
            graduation_year=2025,
            application_deadline=timezone.now() + datetime.timedelta(days=30)
        )
        job.required_skills.add(python, django)

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
"""
with open(cmd_dir / "seed_demo.py", "w") as f:
    f.write(seed_demo_code)

# create __init__.py files
with open(BASE_DIR / "jobs" / "management" / "__init__.py", "w") as f: pass
with open(BASE_DIR / "jobs" / "management" / "commands" / "__init__.py", "w") as f: pass
