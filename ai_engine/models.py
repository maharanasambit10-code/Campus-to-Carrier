
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


class FlightSimulationChallenge(models.Model):
    DIFFICULTY_CHOICES = (
        ('BEGINNER', 'Beginner (Entry-Level / Intern)'),
        ('INTERMEDIATE', 'Intermediate (1-2 yrs experience)'),
        ('ADVANCED', 'Advanced (Senior / High Bar)'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    target_role = models.CharField(max_length=150)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='INTERMEDIATE')
    estimated_minutes = models.PositiveIntegerField(default=30)
    scenario_brief = models.TextField(help_text="Realistic workplace scenario and context.")
    problem_statement = models.TextField(help_text="Specific problem to solve or analyze.")
    dataset_or_context = models.TextField(blank=True, help_text="Sample dataset, code snippet, or operational logs.")
    deliverables_required = models.TextField(help_text="Expected deliverables from candidate.")
    rubric_criteria = models.JSONField(default=list, blank=True)
    skills_tested = models.JSONField(default=list, blank=True)
    badge_name = models.CharField(max_length=120, default='Role-Ready Simulator Badge')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.target_role})"


class SimulationSubmission(models.Model):
    STATUS_CHOICES = (
        ('SUBMITTED', 'Submitted'),
        ('EVALUATED', 'Evaluated'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='simulation_submissions')
    challenge = models.ForeignKey(FlightSimulationChallenge, on_delete=models.CASCADE, related_name='submissions')
    solution_text = models.TextField(help_text="Candidate's solution, code, or analysis.")
    recommendations = models.TextField(blank=True, help_text="Actionable business/technical recommendations.")
    artifact_url = models.URLField(blank=True, help_text="External link to repo, notebook, or demo.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='EVALUATED')
    overall_score = models.PositiveIntegerField(default=85)
    execution_score = models.PositiveIntegerField(default=85)
    problem_solving_score = models.PositiveIntegerField(default=85)
    business_impact_score = models.PositiveIntegerField(default=85)
    rigor_score = models.PositiveIntegerField(default=85)
    demonstrated_strengths = models.JSONField(default=list, blank=True)
    skill_gaps = models.JSONField(default=list, blank=True)
    next_practice_mission = models.JSONField(default=dict, blank=True)
    ai_feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.user.username} - {self.challenge.title} ({self.overall_score}/100)"


class OpportunityCompilerSession(models.Model):
    SCHEDULE_CHOICES = (
        ('5_DAY_SPRINT', '5-Day Intensive Sprint (~15 hrs/wk)'),
        ('2_WEEK_SPRINT', '2-Week Balanced Sprint (~8 hrs/wk)'),
        ('4_WEEK_SPRINT', '4-Week Flexible Sprint (~4 hrs/wk)'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='compiled_opportunities')
    job = models.ForeignKey('jobs.Job', null=True, blank=True, on_delete=models.SET_NULL, related_name='compiled_sessions')
    target_role_title = models.CharField(max_length=200)
    target_company = models.CharField(max_length=200, blank=True)
    job_description_raw = models.TextField(blank=True)
    plain_language_skills = models.JSONField(default=list, blank=True)
    evidence_mapping = models.JSONField(default=list, blank=True)
    readiness_percentage = models.PositiveIntegerField(default=75)
    schedule_type = models.CharField(max_length=30, choices=SCHEDULE_CHOICES, default='2_WEEK_SPRINT')
    available_hours_per_week = models.PositiveIntegerField(default=10)
    sprint_plan = models.JSONField(default=list, blank=True)
    proof_brief_token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.target_role_title} compiled for {self.student.user.username} ({self.readiness_percentage}%)"


class ProofPassport(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='proof_passport')
    headline = models.CharField(max_length=255, default='Role-Ready Candidate Evidence')
    public_share_token = models.CharField(max_length=64, unique=True)
    is_public = models.BooleanField(default=True)
    allowed_employers = models.TextField(blank=True, help_text="Comma-separated employer names or blank for all.")
    include_simulations = models.BooleanField(default=True)
    include_projects = models.BooleanField(default=True)
    include_coursework = models.BooleanField(default=True)
    include_peer_reviews = models.BooleanField(default=True)
    overall_evidence_score = models.PositiveIntegerField(default=85)
    demonstrated_skills_count = models.PositiveIntegerField(default=0)
    inferred_skills_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Proof Passport: {self.student.user.username} (Score {self.overall_evidence_score}%)"


class PassportArtifact(models.Model):
    TYPE_CHOICES = (
        ('SIMULATION', 'Work Simulation (Career Flight Simulator)'),
        ('PROJECT', 'Project Artifact'),
        ('COURSEWORK', 'Coursework & Capstone'),
        ('PEER_REVIEW', 'Peer / Mentor Contribution'),
        ('CERTIFICATION', 'Verified Certification'),
    )
    CONFIDENCE_CHOICES = (
        ('DEMONSTRATED', 'Demonstrated (Work-backed)'),
        ('INFERRED', 'Inferred (Profile / Resume claim)'),
    )

    passport = models.ForeignKey(ProofPassport, on_delete=models.CASCADE, related_name='artifacts')
    artifact_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='PROJECT')
    title = models.CharField(max_length=255)
    description = models.TextField()
    source_reference = models.CharField(max_length=255)
    external_url = models.URLField(blank=True)
    confidence_level = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES, default='DEMONSTRATED')
    skills_evidenced = models.JSONField(default=list, blank=True)
    score_or_grade = models.CharField(max_length=50, blank=True)
    is_pinned = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.get_artifact_type_display()}]"


class PeerContributionReview(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='peer_reviews')
    reviewer_name = models.CharField(max_length=150)
    reviewer_role = models.CharField(max_length=150)
    project_name = models.CharField(max_length=200)
    review_text = models.TextField()
    skills_endorsed = models.JSONField(default=list, blank=True)
    verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.reviewer_name} for {self.student.user.username}"

