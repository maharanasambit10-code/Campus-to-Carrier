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
    match_percentage = models.IntegerField(default=0, help_text="Skill match percentage")
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)

    # Application form submission fields
    full_name = models.CharField(max_length=150, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=30, blank=True, default='')
    degree_major = models.CharField(max_length=150, blank=True, default='')
    cgpa = models.FloatField(null=True, blank=True)
    college = models.CharField(max_length=200, blank=True, default='')
    portfolio_url = models.URLField(blank=True, default='')
    github_url = models.URLField(blank=True, default='')
    linkedin_url = models.URLField(blank=True, default='')
    cover_letter = models.TextField(blank=True, default='')
    availability = models.CharField(max_length=100, blank=True, default='Immediate')
    expected_salary = models.CharField(max_length=100, blank=True, default='')
    experience_level = models.CharField(max_length=100, blank=True, default='Fresher')
    custom_resume = models.FileField(upload_to='application_resumes/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'job')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name or self.student.user.username} applied to {self.job.title}"
