from django.db import models


class Company(models.Model):
    VERIFICATION_CHOICES = (
        ('PENDING', 'Verification Pending'),
        ('VERIFIED', 'Verified Company'),
        ('REJECTED', 'Rejected'),
    )
    COMPANY_TYPE_CHOICES = (
        ('Startup', 'High-Growth Startup'),
        ('Unicorn', 'Tech Unicorn'),
        ('Enterprise', 'Enterprise / MNC'),
        ('Product Lab', 'Product & Research Lab'),
    )

    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=120, blank=True)
    company_type = models.CharField(max_length=50, choices=COMPANY_TYPE_CHOICES, default='Startup')
    tagline = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    locations = models.CharField(max_length=255, blank=True)
    tech_stack = models.CharField(max_length=255, blank=True, default='')
    funding_stage = models.CharField(max_length=80, blank=True, default='Series A / Funded')
    employee_count = models.CharField(max_length=80, blank=True, default='50-200 members')
    hiring_process = models.TextField(blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='VERIFIED')
    is_demo = models.BooleanField(default=False)
    open_positions = models.IntegerField(default=0)
    internship_opportunities = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CompanyConnection(models.Model):
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='company_connections')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='connections')
    preferred_role = models.CharField(max_length=150, blank=True, default='')
    note = models.TextField(blank=True, default='')
    status = models.CharField(max_length=30, default='CONNECTED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'company')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.user.username} <-> {self.company.name}"
