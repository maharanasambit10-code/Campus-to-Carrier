from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime

from accounts.models import User
from students.models import StudentProfile, Skill, StudentSkill
from companies.models import Company, CompanyConnection
from jobs.models import Job
from applications.models import Application


class JobAndStartupConnectTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create student user
        self.user = User.objects.create_user(
            username='teststudent',
            email='teststudent@example.com',
            password='testpassword123',
            role='STUDENT',
            first_name='Aarav',
            last_name='Sharma',
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            cgpa=8.8,
            graduation_year=2026,
            degree='B.Tech Computer Science',
            phone='+91 9876543210',
            college='BPUT University',
        )

        # Create skills
        self.skill_python = Skill.objects.create(name='Python')
        self.skill_django = Skill.objects.create(name='Django')
        StudentSkill.objects.create(student=self.profile, skill=self.skill_python, proficiency=90)

        # Create startups
        self.startup = Company.objects.create(
            name='Sarvam AI',
            company_type='Startup',
            industry='Artificial Intelligence',
            tagline='Indic Foundation LLMs',
            locations='Bengaluru',
            tech_stack='Python, PyTorch, CUDA, FastAPI',
            verification_status='VERIFIED',
        )

        self.unicorn = Company.objects.create(
            name='CRED',
            company_type='Unicorn',
            industry='FinTech',
            tagline='High-Trust Financial Rails',
            locations='Bengaluru',
            tech_stack='Java, Go, Kafka',
            verification_status='VERIFIED',
        )

        # Create jobs
        self.job1 = Job.objects.create(
            title='AI Research Engineer',
            company=self.startup,
            description='Build sovereign language models.',
            location='Bengaluru',
            salary='₹18–28 LPA',
            job_type='Full-Time',
            work_mode='Hybrid',
            minimum_cgpa=7.0,
            graduation_year=2026,
            application_deadline=timezone.now() + datetime.timedelta(days=30),
        )
        self.job1.required_skills.add(self.skill_python)

        self.job2 = Job.objects.create(
            title='Backend SDE-1',
            company=self.unicorn,
            description='Build low-latency microservices.',
            location='Bengaluru',
            salary='₹16–24 LPA',
            job_type='Full-Time',
            work_mode='Onsite',
            minimum_cgpa=7.0,
            graduation_year=2026,
            application_deadline=timezone.now() + datetime.timedelta(days=30),
        )

    def test_job_list_view(self):
        self.client.login(username='teststudent', password='testpassword123')
        response = self.client.get(reverse('job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Research Engineer')
        self.assertContains(response, 'Sarvam AI')
        self.assertContains(response, 'CRED')

    def test_job_list_filter_startup(self):
        self.client.login(username='teststudent', password='testpassword123')
        response = self.client.get(reverse('job_list') + '?company_type=Startup')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sarvam AI')
        self.assertNotContains(response, 'Backend SDE-1')

    def test_job_detail_view(self):
        self.client.login(username='teststudent', password='testpassword123')
        response = self.client.get(reverse('job_detail', kwargs={'job_id': self.job1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Research Engineer')
        self.assertContains(response, 'Sarvam AI')

    def test_apply_job_get_form(self):
        self.client.login(username='teststudent', password='testpassword123')
        response = self.client.get(reverse('apply_job', kwargs={'job_id': self.job1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student/job_apply.html')
        self.assertContains(response, 'Job Application Form')
        self.assertContains(response, 'Aarav Sharma')

    def test_apply_job_post_submission(self):
        self.client.login(username='teststudent', password='testpassword123')
        post_data = {
            'full_name': 'Aarav Sharma',
            'email': 'teststudent@example.com',
            'phone': '+91 9876543210',
            'degree_major': 'B.Tech CSE',
            'college': 'BPUT University',
            'cgpa': '8.8',
            'portfolio_url': 'https://aarav.dev',
            'github_url': 'https://github.com/aarav',
            'cover_letter': 'Excited to contribute to Indian LLMs with my deep PyTorch knowledge.',
            'availability': 'Immediate',
            'experience_level': 'Fresher',
            'expected_salary': '₹20 LPA',
        }
        response = self.client.post(reverse('apply_job', kwargs={'job_id': self.job1.id}), post_data)
        self.assertRedirects(response, reverse('student_applications'))

        # Verify application created with form values
        app = Application.objects.get(student=self.profile, job=self.job1)
        self.assertEqual(app.full_name, 'Aarav Sharma')
        self.assertEqual(app.cover_letter, 'Excited to contribute to Indian LLMs with my deep PyTorch knowledge.')
        self.assertEqual(app.availability, 'Immediate')
        self.assertEqual(app.cgpa, 8.8)

    def test_apply_job_ajax_submission(self):
        self.client.login(username='teststudent', password='testpassword123')
        post_data = {
            'ajax': '1',
            'full_name': 'Aarav Sharma',
            'email': 'teststudent@example.com',
            'phone': '+91 9876543210',
            'degree_major': 'B.Tech CSE',
            'college': 'BPUT University',
            'cover_letter': 'Passionate about microservices architecture and Kafka pipelines.',
        }
        response = self.client.post(
            reverse('apply_job', kwargs={'job_id': self.job2.id}),
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('submitted successfully', data['message'])

    def test_connect_startup_company(self):
        self.client.login(username='teststudent', password='testpassword123')
        post_data = {
            'preferred_role': 'AI / ML Engineer',
            'note': 'Huge admirer of your Indic language model papers!',
        }
        response = self.client.post(
            reverse('connect_company', kwargs={'company_id': self.startup.id}),
            post_data,
        )
        self.assertTrue(
            CompanyConnection.objects.filter(student=self.profile, company=self.startup).exists()
        )
        conn = CompanyConnection.objects.get(student=self.profile, company=self.startup)
        self.assertEqual(conn.preferred_role, 'AI / ML Engineer')
