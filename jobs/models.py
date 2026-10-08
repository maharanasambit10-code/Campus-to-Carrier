import re
from django.db import models
from companies.models import Company
from students.models import Skill


class Job(models.Model):
    WORK_MODE_CHOICES = (
        ('Onsite', 'Onsite'),
        ('Hybrid', 'Hybrid'),
        ('Remote', 'Remote'),
    )

    INTERNSHIP_TYPE_CHOICES = (
        ('Full-Time', 'Full-Time'),
        ('Internship', 'Internship'),
        ('Contract', 'Contract'),
    )

    title = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    description = models.TextField()
    location = models.CharField(max_length=255)
    job_type = models.CharField(max_length=100, default='Full-Time')
    salary = models.CharField(max_length=100, blank=True)
    minimum_cgpa = models.FloatField(default=0.0)
    maximum_backlogs = models.IntegerField(default=0)
    graduation_year = models.IntegerField(default=2026)
    eligible_degree = models.CharField(max_length=160, blank=True)
    experience_required = models.FloatField(default=0.0)
    experience_text = models.CharField(max_length=100, blank=True, default='')
    qualifications = models.TextField(blank=True, default='')
    required_programming_languages = models.CharField(max_length=500, blank=True)
    required_frameworks = models.CharField(max_length=500, blank=True)
    required_technologies = models.CharField(max_length=500, blank=True)
    min_tenth = models.FloatField(default=0.0)
    min_twelfth = models.FloatField(default=0.0)
    allowed_departments = models.CharField(max_length=255, blank=True)
    preferred_skills = models.ManyToManyField(Skill, related_name='preferred_jobs', blank=True)
    required_skills = models.ManyToManyField(Skill, related_name='required_jobs')
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='Onsite')
    internship_type = models.CharField(max_length=20, choices=INTERNSHIP_TYPE_CHOICES, default='Full-Time')
    application_deadline = models.DateTimeField()
    is_verified = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    @property
    def eligible_student_count(self):
        from students.models import StudentProfile
        qs = StudentProfile.objects.filter(cgpa__gte=self.minimum_cgpa or 0, graduation_year__gte=self.graduation_year)
        return qs.count()

    def all_skills_list(self):
        """Returns a combined list of all required skill names for badge display and matching"""
        skills = []
        for s in self.required_skills.all():
            if s.name not in skills:
                skills.append(s.name)
        # Parse extra language/framework fields if present
        for text in (self.required_programming_languages, self.required_frameworks, self.required_technologies):
            if text:
                for item in re.split(r'[,/|]+', text):
                    cleaned = item.strip()
                    if cleaned and cleaned not in skills:
                        skills.append(cleaned)
        return skills


class SavedJob(models.Model):
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by_students')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'job')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.user.username} saved {self.job.title}"
