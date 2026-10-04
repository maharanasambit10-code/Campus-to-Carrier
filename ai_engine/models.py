
from django.db import models
from students.models import StudentProfile

class ResumeAnalysis(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='resume_analysis')
    ats_score = models.IntegerField(default=0)
    extracted_text = models.TextField(blank=True)
    extracted_name = models.CharField(max_length=200, blank=True)
    education = models.TextField(blank=True)
    degree = models.CharField(max_length=160, blank=True)
    college = models.CharField(max_length=240, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    skills = models.JSONField(default=list, blank=True)
    programming_languages = models.JSONField(default=list, blank=True)
    frameworks = models.JSONField(default=list, blank=True)
    databases = models.JSONField(default=list, blank=True)
    tools = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    relevant_keywords = models.JSONField(default=list, blank=True)
    analysis_result = models.JSONField(default=dict, blank=True)
    parse_error = models.CharField(max_length=300, blank=True)
    missing_keywords = models.TextField(blank=True)
    improvement_suggestions = models.TextField(blank=True)
    analyzed_at = models.DateTimeField(auto_now=True)

class PlacementPrediction(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    placement_probability = models.FloatField(default=0.0)
    influencing_factors = models.TextField(blank=True)
    predicted_at = models.DateTimeField(auto_now=True)
