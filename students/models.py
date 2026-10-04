
from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class StudentProfile(models.Model):
    JOB_TYPE_CHOICES = (
        ('INTERNSHIP', 'Internship'),
        ('FULL_TIME', 'Full-time'),
        ('BOTH', 'Internship and full-time'),
    )
    WORK_LOCATION_CHOICES = (
        ('REMOTE', 'Remote'),
        ('HYBRID', 'Hybrid'),
        ('ONSITE', 'On-site'),
    )
    VISIBILITY_CHOICES = (
        ('VERIFIED_RECRUITERS', 'Public to Verified Recruiters'),
        ('PRIVATE', 'Private'),
        ('APPLICATIONS_ONLY', 'Only During Applications'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    degree = models.CharField(max_length=120, blank=True)
    specialization = models.CharField(max_length=160, blank=True)
    current_semester = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    college = models.CharField(max_length=200, blank=True)
    headline = models.CharField(max_length=180, blank=True)
    education_start_year = models.IntegerField(null=True, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    cgpa = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])
    tenth_percentage = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    twelfth_percentage = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    tenth_school = models.CharField(max_length=200, blank=True)
    tenth_year = models.IntegerField(null=True, blank=True)
    twelfth_college = models.CharField(max_length=200, blank=True)
    twelfth_year = models.IntegerField(null=True, blank=True)
    active_backlogs = models.IntegerField(default=0)
    location = models.CharField(max_length=200, blank=True)
    about_me = models.TextField(blank=True)
    career_objective = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    skills = models.ManyToManyField(Skill, through='StudentSkill')
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)
    leetcode = models.URLField(blank=True)
    codechef = models.URLField(blank=True)
    hackerrank = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    preferred_job_role = models.CharField(max_length=160, blank=True)
    preferred_domain = models.CharField(max_length=160, blank=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, blank=True)
    preferred_work_location = models.CharField(max_length=20, choices=WORK_LOCATION_CHOICES, blank=True)
    profile_visibility = models.CharField(max_length=24, choices=VISIBILITY_CHOICES, default='VERIFIED_RECRUITERS')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def completion_percentage(self):
        sections = self.profile_strength
        return round(sum(sections.values()))

    @property
    def profile_strength(self):
        return {
            'basic_information': 15 if all([self.user.get_full_name(), self.user.email, self.phone, self.location]) else 0,
            'education': 15 if all([self.department, self.college, self.graduation_year, self.cgpa]) else 0,
            'skills': 15 if self.studentskill_set.exists() else 0,
            'projects': 15 if self.projects.exists() else 0,
            'resume': 15 if self.resume else 0,
            'certifications': 10 if self.certifications.exists() else 0,
            'experience': 5 if self.internships.exists() else 0,
            'professional_links': 5 if any([self.linkedin, self.github, self.portfolio]) else 0,
            'about_objective': 5 if self.about_me and self.career_objective else 0,
        }

class StudentSkill(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.IntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'skill'], name='unique_student_skill'),
        ]


class Project(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    description = models.TextField()
    technologies = models.CharField(max_length=200)
    project_type = models.CharField(max_length=80, blank=True)
    role = models.CharField(max_length=120, blank=True)
    github_url = models.URLField(blank=True)
    live_demo_url = models.URLField(blank=True)
    image = models.ImageField(upload_to='projects/', blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-end_date', '-start_date', '-id']
    
class Internship(models.Model):
    EMPLOYMENT_TYPES = (
        ('INTERNSHIP', 'Internship'),
        ('FULL_TIME', 'Full-time'),
        ('PART_TIME', 'Part-time'),
        ('FREELANCE', 'Freelance'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='internships')
    company = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='INTERNSHIP')
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField()
    skills_used = models.CharField(max_length=300, blank=True)

class Certification(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    issue_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=160, blank=True)
    credential_url = models.URLField(blank=True)
    certificate_file = models.FileField(upload_to='certifications/', blank=True, null=True)


class Achievement(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    achieved_on = models.DateField(null=True, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    proof_url = models.URLField(blank=True)

    class Meta:
        ordering = ['-achieved_on', '-id']
