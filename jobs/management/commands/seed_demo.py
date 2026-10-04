
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
        skill_names = [
            'Python', 'Django', 'REST API', 'SQL', 'PostgreSQL', 'Machine Learning',
            'NumPy', 'Pandas', 'Scikit-learn', 'TensorFlow', 'Deep Learning',
            'APIs', 'LLM', 'RAG', 'LangChain', 'AI', 'Cloud',
        ]
        skills = {name: Skill.objects.get_or_create(name=name)[0] for name in skill_names}
        
        # Company
        company, _ = Company.objects.get_or_create(name="Tech Innovations Inc.", description="A leading tech company.", website="https://techinnovations.example.com")
        
        # Users
        student_user, _ = User.objects.get_or_create(username="student1", email="student1@example.com", role="STUDENT")
        student_user.set_password("password123")
        student_user.save()
        
        recruiter_user, _ = User.objects.get_or_create(username="recruiter1", email="recruiter@example.com", role="RECRUITER")
        recruiter_user.set_password("password123")
        recruiter_user.save()

        officer_user, _ = User.objects.get_or_create(username="officer1", email="officer@example.com", role="PLACEMENT_OFFICER")
        officer_user.set_password("password123")
        officer_user.save()

        bapuni_user, _ = User.objects.get_or_create(
            username="bapuni_123",
            defaults={"email": "bapuni_123@example.com", "role": "STUDENT"},
        )
        bapuni_user.role = "STUDENT"
        bapuni_user.set_password("Bapuni@123")
        bapuni_user.save()


        # Profiles
        student_profile, _ = StudentProfile.objects.get_or_create(user=student_user, cgpa=8.5, graduation_year=2025, department="Computer Science")
        StudentProfile.objects.get_or_create(user=bapuni_user)
        StudentSkill.objects.get_or_create(student=student_profile, skill=skills['Python'], proficiency=90)
        StudentSkill.objects.get_or_create(student=student_profile, skill=skills['Django'], proficiency=85)
        
        RecruiterProfile.objects.get_or_create(user=recruiter_user, company=company, designation="Senior Technical Recruiter")
        
        # Jobs
        from django.utils import timezone
        import datetime
        demo_jobs = [
            ('Python Developer', 'Build Python services and REST APIs for a growing product team.', 'Bhubaneswar', '₹6–10 LPA', 'Full-Time', ['Python', 'Django', 'REST API', 'SQL']),
            ('Django Backend Developer', 'Develop secure backend systems and data services with Django.', 'Bengaluru', '₹8–14 LPA', 'Full-Time', ['Python', 'Django', 'PostgreSQL', 'REST API']),
            ('Junior AI/ML Engineer', 'Support model development, evaluation and data preparation workflows.', 'Hyderabad', '₹7–12 LPA', 'Full-Time', ['Python', 'Machine Learning', 'NumPy', 'Pandas', 'Scikit-learn']),
            ('Machine Learning Engineer', 'Productionize predictive models with strong engineering practices.', 'Pune', '₹10–18 LPA', 'Full-Time', ['Python', 'Scikit-learn', 'TensorFlow', 'Machine Learning']),
            ('AI Engineer', 'Prototype and ship intelligent APIs and deep learning solutions.', 'Remote', '₹9–16 LPA', 'Full-Time', ['Python', 'Machine Learning', 'Deep Learning', 'APIs']),
            ('Data Scientist', 'Turn product data into insights, experiments and measurable decisions.', 'Bengaluru', '₹8–15 LPA', 'Full-Time', ['Python', 'Pandas', 'NumPy', 'SQL', 'Machine Learning']),
            ('Generative AI Engineer', 'Build retrieval-augmented experiences with modern language models.', 'Hyderabad', '₹12–22 LPA', 'Full-Time', ['Python', 'LLM', 'RAG', 'APIs', 'LangChain']),
            ('Backend Python Developer', 'Create scalable Django services and reliable integrations.', 'Pune', '₹7–13 LPA', 'Full-Time', ['Python', 'Django', 'REST API', 'PostgreSQL']),
            ('Junior Machine Learning Engineer', 'Collaborate on feature engineering, training and model analysis.', 'Remote', '₹6–11 LPA', 'Internship', ['Python', 'Machine Learning', 'Scikit-learn', 'Pandas']),
            ('AI Software Engineer', 'Deliver production software across AI, APIs and cloud platforms.', 'Bhubaneswar', '₹10–19 LPA', 'Full-Time', ['Python', 'AI', 'REST API', 'SQL', 'Cloud']),
        ]
        deadline = timezone.now() + datetime.timedelta(days=30)
        for title, description, location, salary, job_type, job_skill_names in demo_jobs:
            job, _ = Job.objects.get_or_create(
                title=title,
                company=company,
                defaults={
                    'description': description,
                    'location': location,
                    'salary': salary,
                    'job_type': job_type,
                    'minimum_cgpa': 7.0,
                    'graduation_year': 2026,
                    'application_deadline': deadline,
                },
            )
            job.required_skills.set([skills[name] for name in job_skill_names])

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
