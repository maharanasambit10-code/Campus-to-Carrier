from decimal import Decimal
from django.db import models
from accounts.models import User
from applications.models import Application


class Interview(models.Model):
	MODE_CHOICES = (
		('ONLINE', 'Online'),
		('ONSITE', 'Onsite'),
	)
	STATUS_CHOICES = (
		('SCHEDULED', 'Scheduled'),
		('COMPLETED', 'Completed'),
		('CANCELLED', 'Cancelled'),
	)

	application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
	round_name = models.CharField(max_length=120, default='Technical Interview')
	scheduled_at = models.DateTimeField()
	duration_minutes = models.PositiveIntegerField(default=45)
	mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='ONLINE')
	meeting_link = models.URLField(blank=True)
	location = models.CharField(max_length=255, blank=True)
	status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='SCHEDULED')
	interviewer_notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['scheduled_at']

	def __str__(self):
		return f'{self.application.student.user.username} - {self.round_name}'


class MockInterviewSession(models.Model):
	INTERVIEW_TYPE_CHOICES = (
		('HR', 'HR & Culture Fit'),
		('TECHNICAL', 'Technical & Problem Solving'),
		('BEHAVIORAL', 'Behavioral (STAR Method)'),
		('CASE', 'Case Study & Estimation'),
	)
	DIFFICULTY_CHOICES = (
		('BEGINNER', 'Beginner (Internship / Entry Level)'),
		('INTERMEDIATE', 'Intermediate (1-2 yrs experience)'),
		('ADVANCED', 'Advanced (Senior / High Bar)'),
	)

	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mock_interviews')
	role_target = models.CharField(max_length=150, default='Software Engineer Intern')
	company_type = models.CharField(max_length=150, default='Tech Product Startup')
	interview_type = models.CharField(max_length=50, choices=INTERVIEW_TYPE_CHOICES, default='HR')
	difficulty = models.CharField(max_length=30, choices=DIFFICULTY_CHOICES, default='BEGINNER')
	duration_minutes = models.PositiveIntegerField(default=15)
	overall_score = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('0.0'))
	communication_score = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('0.0'))
	content_score = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('0.0'))
	confidence_score = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('0.0'))
	body_language_score = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('0.0'))
	strengths = models.JSONField(default=list, blank=True)
	areas_for_improvement = models.JSONField(default=list, blank=True)
	sample_answer = models.TextField(blank=True)
	practice_plan = models.JSONField(default=list, blank=True)
	transcript = models.JSONField(default=list, blank=True)
	observations = models.JSONField(default=dict, blank=True)
	status = models.CharField(max_length=20, default='COMPLETED')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.user.username} - {self.role_target} ({self.get_interview_type_display()}) - {self.overall_score}/10"

