from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from docx import Document

from accounts.models import Membership, User
from companies.models import Company
from jobs.models import Job
from students.models import Skill, StudentProfile, StudentSkill
from .models import ResumeAnalysis
from .services import match_jobs


class CareerMatchTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='student', password='password')
		Membership.objects.create(user=self.user, plan='PRO_MONTHLY', status='ACTIVE')
		self.profile = StudentProfile.objects.create(user=self.user, degree='B.Tech', cgpa=8.0)
		for name in ('Python', 'Django', 'SQL'):
			skill = Skill.objects.create(name=name)
			StudentSkill.objects.create(student=self.profile, skill=skill)
		Skill.objects.create(name='React')
		company = Company.objects.create(name='Campus Tech')
		self.job = Job.objects.create(
			company=company,
			title='Python Developer',
			description='Backend role',
			location='Remote',
			graduation_year=2026,
			application_deadline='2027-01-01T00:00:00Z',
		)
		self.job.required_skills.set(Skill.objects.filter(name__in=['Python', 'Django', 'SQL', 'React']))

	def test_partial_match_exposes_missing_skills(self):
		match = match_jobs(self.profile, [self.job])[0]
		self.assertEqual(match['score'], 75)
		self.assertEqual(match['status'], 'PARTIAL MATCH')
		self.assertEqual(match['missing_skills'], ['react'])

	def test_docx_upload_creates_structured_analysis(self):
		document = Document()
		document.add_paragraph('Asha Student')
		document.add_paragraph('B.Tech Computer Science 2026')
		document.add_paragraph('Python Django SQL Git')
		content = BytesIO()
		document.save(content)
		upload = SimpleUploadedFile('resume.docx', content.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

		self.client.force_login(self.user)
		response = self.client.post('/student/career-match/', {'resume': upload})

		self.assertEqual(response.status_code, 302)
		analysis = ResumeAnalysis.objects.get(student=self.profile)
		self.assertIn('Python', analysis.skills)
		self.assertFalse(analysis.parse_error)
		page = self.client.get('/student/career-match/')
		self.assertEqual(page.status_code, 200)

# Create your tests here.
