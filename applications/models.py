
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
