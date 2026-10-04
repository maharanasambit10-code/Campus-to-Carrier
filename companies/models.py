
from django.db import models


class Company(models.Model):
    VERIFICATION_CHOICES = (
        ('PENDING', 'Verification Pending'),
        ('VERIFIED', 'Verified Company'),
        ('REJECTED', 'Rejected'),
    )

    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    locations = models.CharField(max_length=255, blank=True)
    hiring_process = models.TextField(blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='PENDING')
    is_demo = models.BooleanField(default=True)
    open_positions = models.IntegerField(default=0)
    internship_opportunities = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
