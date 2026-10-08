from django.db import models
from .logos import resolve_company_logo, get_company_initials, get_company_brand_color


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
    logo_url = models.URLField(max_length=500, blank=True, default='', help_text="Direct vector/CDN logo URL")
    headquarters = models.CharField(max_length=255, blank=True, default='')
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

    @property
    def get_logo_url(self):
        return resolve_company_logo(self)

    @property
    def initials(self):
        return get_company_initials(self.name)

    @property
    def brand_color(self):
        return get_company_brand_color(self.name)

    def get_required_skills(self):
        """Returns unique list of skills demanded by this company's jobs"""
        skills_set = set()
        for job in self.jobs.filter(is_verified=True).prefetch_related('required_skills'):
            for sk in job.required_skills.all():
                skills_set.add(sk.name)
        if not skills_set and self.tech_stack:
            for item in self.tech_stack.split(','):
                cleaned = item.strip()
                if cleaned:
                    skills_set.add(cleaned)
        return sorted(skills_set)


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
