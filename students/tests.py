from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import TestCase
from PIL import Image

from accounts.models import User
from .models import Project, Skill, StudentProfile, StudentSkill


class StudentProfileTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='student-one',
			email='student@example.com',
			password='test-password-123',
			first_name='Ada',
			last_name='Lovelace',
		)
		self.client.force_login(self.user)

	def test_profile_page_creates_profile_and_renders(self):
		response = self.client.get(reverse('student_profile'))

		self.assertEqual(response.status_code, 200)
		self.assertTrue(StudentProfile.objects.filter(user=self.user).exists())
		self.assertContains(response, 'Build your professional story')

	def test_career_match_renders_without_resume_analysis(self):
		response = self.client.get(reverse('career_match'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Resume analyzed: No')
		self.assertContains(response, 'Education')

	def test_dashboard_exposes_profile_and_resume_toolkit(self):
		response = self.client.get(reverse('student_dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'ATS readiness')
		self.assertContains(response, 'Profile checklist')
		self.assertContains(response, 'Analyze resume')

	def test_interview_page_exposes_preparation_workspace(self):
		response = self.client.get(reverse('interview_list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Interview preparation')
		self.assertContains(response, 'Prepare with confidence')

	def test_applications_shows_student_registration_cta(self):
		response = self.client.get(reverse('student_applications'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '+ Student Registration')
		self.assertContains(response, f'href="{reverse("student_register")}"')

	def test_student_registration_form_is_available_from_authenticated_session(self):
		response = self.client.get(reverse('student_register'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Student Registration')
		self.assertContains(response, 'Create Student Account')
		self.assertContains(response, 'Already have an account?')

	def test_profile_update_and_project_creation_are_persisted(self):
		self.client.post(reverse('student_profile'), {
			'phone': '5550100',
			'department': 'Computer Science',
			'college': 'Campus University',
			'graduation_year': '2027',
			'cgpa': '8.8',
			'tenth_percentage': '92',
			'twelfth_percentage': '90',
			'location': 'Bengaluru',
			'about_me': 'Backend developer.',
			'career_objective': 'Build useful software.',
			'linkedin': 'https://www.linkedin.com/in/ada',
			'github': 'https://github.com/ada',
			'portfolio': 'https://ada.example.com',
			'leetcode': 'https://leetcode.com/ada',
		})
		profile = StudentProfile.objects.get(user=self.user)
		self.assertEqual(profile.college, 'Campus University')
		self.assertEqual(profile.cgpa, 8.8)

		response = self.client.post(reverse('save_project'), {
			'name': 'Placement Portal',
			'description': 'A Django placement platform.',
			'technologies': 'Django, Bootstrap',
			'github_url': 'https://github.com/ada/placement-portal',
			'live_demo_url': 'https://placement.example.com',
			'start_date': '2026-01-01',
			'end_date': '2026-06-01',
		})

		self.assertRedirects(response, reverse('student_profile'))
		project = Project.objects.get(student=profile)
		self.assertEqual(project.name, 'Placement Portal')
		self.assertGreater(response.wsgi_request.user.student_profile.id, 0)

	def test_profile_photo_upload_is_saved(self):
		img = Image.new('RGB', (300, 300), color=(12, 34, 56))
		buffer = BytesIO()
		img.save(buffer, format='PNG')
		buffer.seek(0)

		response = self.client.post(reverse('student_profile'), {
			'phone': '8093568055',
			'department': 'Computer Science',
			'college': 'Biju Patnaik University of Technology',
			'graduation_year': '2026',
			'cgpa': '8.7',
			'tenth_percentage': '88',
			'twelfth_percentage': '86',
			'location': 'Bhubaneswar, Odisha',
			'about_me': 'Motivated student.',
			'career_objective': 'Build meaningful software.',
			'linkedin': 'https://www.linkedin.com/in/ada',
			'github': 'https://github.com/ada',
			'portfolio': 'https://ada.example.com',
			'leetcode': 'https://leetcode.com/ada',
			'profile_photo': SimpleUploadedFile('profile.png', buffer.read(), content_type='image/png'),
		})

		self.assertEqual(response.status_code, 302)
		profile = StudentProfile.objects.get(user=self.user)
		self.assertTrue(profile.profile_photo)
		self.assertEqual(profile.phone, '8093568055')
		self.assertEqual(profile.location, 'Bhubaneswar, Odisha')

	def test_project_cannot_be_edited_by_another_student(self):
		profile = StudentProfile.objects.create(user=self.user)
		project = Project.objects.create(
			student=profile,
			name='Private project',
			description='Private details',
			technologies='Python',
		)
		other_user = User.objects.create_user(username='student-two', password='test-password-123')
		self.client.force_login(other_user)

		response = self.client.get(reverse('edit_project', args=[project.id]))

		self.assertEqual(response.status_code, 404)

	def test_skills_field_updates_existing_through_model(self):
		response = self.client.post(reverse('student_profile'), {
			'phone': '8093568055',
			'department': 'Computer Science',
			'college': 'Biju Patnaik University of Technology',
			'graduation_year': '2026',
			'cgpa': '8.7',
			'skills': 'Python, Django, AI Engineering',
		})

		self.assertRedirects(response, reverse('student_profile'))
		profile = StudentProfile.objects.get(user=self.user)
		self.assertEqual(
			set(StudentSkill.objects.filter(student=profile).values_list('skill__name', flat=True)),
			{'Python', 'Django', 'Ai Engineering'},
		)

	def test_completion_uses_requested_profile_signals(self):
		self.client.post(reverse('student_profile'), {
			'phone': '8093568055',
			'department': 'Computer Science',
			'college': 'Biju Patnaik University of Technology',
			'graduation_year': '2026',
			'cgpa': '8.7',
			'tenth_percentage': '88',
			'twelfth_percentage': '86',
			'location': 'Bhubaneswar',
			'about_me': 'Motivated student.',
			'career_objective': 'Build useful software.',
			'skills': 'Python',
			'github': 'https://github.com/ada',
			'linkedin': 'https://www.linkedin.com/in/ada',
			'portfolio': 'https://ada.example.com',
		})

		response = self.client.get(reverse('student_profile'))
		self.assertEqual(response.context['profile_completion'], 88)
