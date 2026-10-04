from django.db import models

from companies.models import Company
from students.models import StudentProfile


class Course(models.Model):
    title = models.CharField(max_length=255)
    provider = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='courses')
    description = models.TextField()
    duration = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=100, blank=True)
    mode = models.CharField(max_length=50, default='Online')
    deadline = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CourseApplication(models.Model):
    STATUS_CHOICES = (
        ('APPLIED', 'Applied'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='course_applications')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_course_application'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student.user.username} - {self.course.title}'
