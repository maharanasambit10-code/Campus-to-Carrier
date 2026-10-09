
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


# =========================================================================
# CAMPUSLINK PROOF INTELLIGENCE PLATFORM (From PDF Presentation)
# =========================================================================

class RoleDecoderAnalysis(models.Model):
    """
    ENGINE 01: ROLE DECODER (Slide 4 & 9)
    Extracts skills, normalized priority weights, experience signals, and must-have vs nice-to-have.
    """
    student = models.ForeignKey(StudentProfile, null=True, blank=True, on_delete=models.CASCADE, related_name='decoded_roles')
    job = models.ForeignKey('jobs.Job', null=True, blank=True, on_delete=models.SET_NULL, related_name='decoder_analyses')
    job_title = models.CharField(max_length=200, default='Junior Data Analyst')
    company_name = models.CharField(max_length=200, blank=True, default='CampusLink Partner Company')
    job_description_raw = models.TextField()
    extracted_skills = models.JSONField(default=list, blank=True)
    must_have_skills = models.JSONField(default=list, blank=True)
    nice_to_have_skills = models.JSONField(default=list, blank=True)
    experience_signals = models.JSONField(default=list, blank=True)
    normalized_weights = models.JSONField(default=dict, blank=True)
    total_skills_count = models.PositiveIntegerField(default=9)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Role Decoder: {self.job_title} ({len(self.extracted_skills)} skills)"


class ProofMinerItem(models.Model):
    """
    ENGINE 02: PROOF MINER (Slide 4, 6 & 10)
    Connects GitHub repos, certificates, mini-tests, project files, and peer/mentor validations.
    """
    PROOF_TYPE_CHOICES = (
        ('GITHUB', 'GitHub Repository / Code Link'),
        ('PROJECT_FILE', 'Project Files / Capstone Artifact'),
        ('CERTIFICATE', 'Verified Certificate / Credential'),
        ('MINI_TEST', 'Mini-Test / Timed Mission'),
        ('MENTOR', 'Peer / Mentor Validation'),
    )
    STRENGTH_CHOICES = (
        ('Strong', 'Strong'),
        ('Medium', 'Medium'),
        ('Inferred', 'Inferred'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='proof_miner_items')
    proof_type = models.CharField(max_length=30, choices=PROOF_TYPE_CHOICES, default='GITHUB')
    title = models.CharField(max_length=255)
    url_or_ref = models.CharField(max_length=500, blank=True)
    skills_connected = models.JSONField(default=list, blank=True)
    evidence_details = models.TextField(blank=True)
    strength = models.CharField(max_length=20, choices=STRENGTH_CHOICES, default='Strong')
    freshness_label = models.CharField(max_length=50, default='Today')  # e.g., "Today", "2 weeks", "1 month", "3 weeks"
    is_demonstrated = models.BooleanField(default=True)
    verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.get_proof_type_display()}] - {self.student.user.username}"


class RoleMission(models.Model):
    """
    AI FEATURE: THE 15-MINUTE ROLE MISSION (Slide 5)
    Instead of asking 'Do you know SQL?', asks the candidate to prove it.
    """
    title = models.CharField(max_length=200, default='The 15-minute Role Mission: Junior Data Analyst')
    slug = models.SlugField(max_length=200, unique=True, default='junior-data-analyst-15m')
    target_role = models.CharField(max_length=150, default='Junior Data Analyst')
    estimated_minutes = models.PositiveIntegerField(default=15)
    scenario_brief = models.TextField(
        default="An e-commerce team sees a 12% drop in repeat purchases. You are tasked with analyzing the drop, inspecting telemetry metrics, and prescribing high-ROI operational interventions."
    )
    task1_prompt = models.TextField(default="TASK 1. Identify 2 metrics you would inspect.")
    task2_prompt = models.TextField(default="TASK 2. Write one SQL query or explain the logic.")
    task3_prompt = models.TextField(default="TASK 3. Give one business action based on the result.")
    skills_tested = models.JSONField(default=list, blank=True)
    default_next_gap = models.CharField(max_length=255, default="JOINs need practice -> 12-min mission")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.target_role})"


class RoleMissionSubmission(models.Model):
    """
    Evaluation for 15-minute Role Mission:
    Grades across Logic, SQL, and Business thinking, captures evidence, and identifies next gap.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mission_submissions')
    mission = models.ForeignKey(RoleMission, on_delete=models.CASCADE, related_name='submissions')
    task1_answer = models.TextField()
    task2_answer = models.TextField()
    task3_answer = models.TextField()
    logic_score = models.PositiveIntegerField(default=80)
    sql_score = models.PositiveIntegerField(default=75)
    business_thinking_score = models.PositiveIntegerField(default=80)
    overall_score = models.PositiveIntegerField(default=78)
    evidence_captured = models.BooleanField(default=True)
    next_gap = models.CharField(max_length=255, default='JOINs need practice -> 12-min mission')
    ai_evaluation_summary = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.user.username} - {self.mission.title} ({self.overall_score}/100)"


class CollegeReadinessRadar(models.Model):
    """
    COLLEGE IMPACT: LIVE READINESS RADAR (Slide 7)
    Live distribution of skills across student body for proactive placement training.
    """
    college_name = models.CharField(max_length=200, default='CampusLink University Network')
    department = models.CharField(max_length=100, default='All Departments')
    sql_avg = models.PositiveIntegerField(default=38)  # 38%
    communication_avg = models.PositiveIntegerField(default=52)  # 52%
    python_avg = models.PositiveIntegerField(default=71)  # 71%
    excel_bi_avg = models.PositiveIntegerField(default=64)  # 64%
    problem_solving_avg = models.PositiveIntegerField(default=78)  # 78%
    total_students_tracked = models.PositiveIntegerField(default=280)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.college_name} Readiness Radar"


class CollegeTargetedIntervention(models.Model):
    """
    Targeted intervention sprint launched by placement team (Slide 7)
    """
    radar = models.ForeignKey(CollegeReadinessRadar, on_delete=models.CASCADE, related_name='interventions', null=True, blank=True)
    skill_target = models.CharField(max_length=100, default='SQL')
    target_cohort = models.CharField(max_length=100, default='Bottom 30%')
    targeted_students_count = models.PositiveIntegerField(default=84)
    mission_assigned = models.CharField(max_length=255, default='Targeted SQL Sprint: 15-min Query & Cohort Challenge')
    status = models.CharField(max_length=50, default='ACTIVE')
    measured_improvement_pct = models.PositiveIntegerField(default=26)
    launched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-launched_at']

    def __str__(self):
        return f"Intervention: {self.skill_target} Sprint ({self.target_cohort})"


class RecruiterCandidateProof(models.Model):
    """
    RECRUITER VIEW: SHORTLIST BY PROOF, NOT KEYWORD DENSITY (Slide 8)
    Comparable evidence and explainable recommendations.
    """
    candidate_name = models.CharField(max_length=150)
    candidate_label = models.CharField(max_length=50, default='Candidate A')  # Candidate A, Candidate B, Candidate C
    target_role = models.CharField(max_length=150, default='Data Analyst')
    role_fit_percentage = models.PositiveIntegerField(default=91)  # 91%, 84%, 76%
    proof_skills_proven = models.CharField(max_length=50, default='9 / 10')  # 9/10, 7/10, 6/10 skills proven
    why_recommended = models.TextField(default='strong evidence on highest-weight skills.')
    evidence_trail = models.JSONField(default=list, blank=True)
    is_shortlisted = models.BooleanField(default=False)
    mission_sent = models.BooleanField(default=False)
    student = models.ForeignKey(StudentProfile, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-role_fit_percentage']

    def __str__(self):
        return f"{self.candidate_label} ({self.candidate_name}) - {self.target_role} ({self.role_fit_percentage}%)"


class PlacementRiskProfile(models.Model):
    """
    FEATURE: PLACEMENT RISK EARLY-WARNING
    Proactively flags at-risk candidates before campus placement season.
    """
    RISK_LEVEL_CHOICES = (
        ('HIGH_RISK', 'High Risk (Immediate Intervention Required)'),
        ('MODERATE_RISK', 'Moderate Risk (Targeted Gaps)'),
        ('PLACEMENT_READY', 'Placement Ready (Strong Evidence Base)'),
    )

    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='placement_risk_profile')
    risk_level = models.CharField(max_length=30, choices=RISK_LEVEL_CHOICES, default='MODERATE_RISK')
    risk_score = models.PositiveIntegerField(default=55)  # 0 to 100, higher = higher risk
    primary_risk_factors = models.JSONField(default=list, blank=True)
    recommended_intervention = models.CharField(max_length=255, default='Targeted SQL Sprint + 15-min Mission')
    intervention_dispatched = models.BooleanField(default=False)
    proof_coverage_ratio = models.CharField(max_length=50, default='4/9 skills verified')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-risk_score']

    def __str__(self):
        return f"Risk: {self.student.user.username} ({self.get_risk_level_display()})"


class InterviewArenaSession(models.Model):
    """
    FEATURE: AI INTERVIEW ARENA
    Interactive real-time interview simulator evaluating Technical Rigor,
    Communication Clarity, Problem Structuring, and Executive Presence.
    Syncs directly to Proof Passport as verified interview proof.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='interview_arena_sessions')
    target_role = models.CharField(max_length=150, default='Junior Data Analyst')
    interview_mode = models.CharField(max_length=50, default='Technical & Scenario Deep Dive')
    question_prompt = models.TextField(default='Explain how you would diagnose a 12% drop in repeat purchases using SQL and cohort analysis.')
    candidate_response = models.TextField()
    technical_rigor_score = models.PositiveIntegerField(default=84)
    communication_clarity_score = models.PositiveIntegerField(default=88)
    problem_structuring_score = models.PositiveIntegerField(default=82)
    overall_score = models.PositiveIntegerField(default=85)
    ai_feedback = models.TextField(blank=True)
    key_strengths = models.JSONField(default=list, blank=True)
    improvement_areas = models.JSONField(default=list, blank=True)
    verified_in_passport = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Arena: {self.student.user.username} - {self.target_role} ({self.overall_score}/100)"


class PersonalizedImprovementAction(models.Model):
    """
    FEATURE: NEXT-BEST ACTION / PERSONALIZED IMPROVEMENT
    Prioritized high-leverage micro-actions ranked by placement ROI.
    """
    CATEGORY_CHOICES = (
        ('ROLE_MISSION', '15-min Role Mission'),
        ('PROOF_MINER', 'Proof Miner Upload'),
        ('INTERVIEW_ARENA', 'AI Interview Arena'),
        ('PEER_REVIEW', 'Mentor Validation'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='improvement_actions')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='ROLE_MISSION')
    target_skill = models.CharField(max_length=100, default='SQL')
    expected_roi_boost = models.CharField(max_length=50, default='+9% Role Fit')
    estimated_minutes = models.PositiveIntegerField(default=15)
    action_url = models.CharField(max_length=255, default='/role-mission/')
    is_completed = models.BooleanField(default=False)
    priority_order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['priority_order', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.expected_roi_boost}) for {self.student.user.username}"


class SkillBarterWallet(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='barter_wallet')
    coins = models.IntegerField(default=5)  # Welcome 5 barter coins
    hours_taught = models.IntegerField(default=0)
    hours_learned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} Wallet ({self.coins} Coins)"


class SkillBarterListing(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open for Barter'),
        ('IN_PROGRESS', 'Exchange in Progress'),
        ('COMPLETED', 'Completed'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='barter_listings')
    offer_skill = models.CharField(max_length=120)   # e.g. DSA, Python, Next.js
    wanted_skill = models.CharField(max_length=120)  # e.g. Spoken English, System Design
    session_hours = models.IntegerField(default=1)
    coins_reward = models.IntegerField(default=1)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    partner = models.ForeignKey(StudentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='barter_matches')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Teach {self.offer_skill} <-> Learn {self.wanted_skill} ({self.student.user.username})"


class LiveCodingStream(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='live_streams')
    anonymous_alias = models.CharField(max_length=120, default='Night-Owl Coder #402')
    language = models.CharField(max_length=80, default='Python / Django')
    problem_title = models.CharField(max_length=255, default='LRU Cache & Concurrency System')
    is_live = models.BooleanField(default=True)
    viewer_count = models.IntegerField(default=18)
    hr_scouts_count = models.IntegerField(default=3)
    code_snippet = models.TextField(default='# Live 2:15 AM Session\nclass LRUCache:\n    def __init__(self, capacity: int):\n        self.capacity = capacity\n        self.cache = {}\n')
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_live', '-started_at']

    def __str__(self):
        return f"{self.anonymous_alias} - {self.problem_title}"


class TpoFairnessVote(models.Model):
    college_name = models.CharField(max_length=200, default='BPUT University')
    student_token = models.CharField(max_length=64, unique=True)
    transparency_rating = models.IntegerField(default=4)  # 1-5 scale
    is_fair_and_unbiased = models.BooleanField(default=True)
    comment = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Vote {self.transparency_rating}/5 for {self.college_name}"




