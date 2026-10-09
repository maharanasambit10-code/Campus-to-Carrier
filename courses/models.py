import uuid
from django.db import models
from django.utils import timezone
from students.models import StudentProfile


CATEGORY_CHOICES = [
    ('programming', 'Programming'),
    ('web', 'Web Development'),
    ('database', 'Database'),
    ('aptitude', 'Aptitude'),
    ('interview', 'Interview Preparation'),
    ('communication', 'Communication Skills'),
]

LEVEL_CHOICES = [
    ('beginner', 'Beginner'),
    ('intermediate', 'Intermediate'),
    ('advanced', 'Advanced'),
]


# ── Legacy models kept for backward compatibility ───────────────────────────────
class Company(models.Model):
    """Minimal stub so old migrations referencing companies.Company still resolve
    via courses app if courses was ever imported with it.  The real Company lives
    in companies/models.py; we just keep the FK-safe import here."""
    pass


# ── Core Learning Hub models ────────────────────────────────────────────────────

class LearningCourse(models.Model):
    """A self-contained learning course on the Learning Hub."""
    title        = models.CharField(max_length=255)
    slug         = models.SlugField(unique=True)
    category     = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='programming')
    description  = models.TextField()
    objectives   = models.TextField(blank=True, help_text='One objective per line')
    level        = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    icon         = models.CharField(max_length=80, default='bi-book', help_text='Bootstrap icon class e.g. bi-python')
    icon_color   = models.CharField(max_length=20, default='#00b4d8')
    icon_bg      = models.CharField(max_length=20, default='#e0f7fa')
    duration_hrs = models.PositiveSmallIntegerField(default=10)
    is_published = models.BooleanField(default=True)
    order        = models.PositiveSmallIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def total_lessons(self):
        return self.lessons.count()

    def get_objectives_list(self):
        return [o.strip() for o in self.objectives.splitlines() if o.strip()]


class Lesson(models.Model):
    """A single lesson inside a LearningCourse."""
    CONTENT_TYPES = [
        ('video', 'Video'),
        ('text', 'Text / Notes'),
        ('pdf', 'PDF Resource'),
    ]
    course       = models.ForeignKey(LearningCourse, on_delete=models.CASCADE, related_name='lessons')
    title        = models.CharField(max_length=255)
    order        = models.PositiveSmallIntegerField(default=0)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, default='text')
    content_text = models.TextField(blank=True, help_text='Lesson notes/HTML content')
    video_url    = models.URLField(blank=True, help_text='Embed URL for YouTube/Vimeo')
    pdf_url      = models.URLField(blank=True, help_text='Link to downloadable PDF')
    duration_min = models.PositiveSmallIntegerField(default=10, help_text='Estimated minutes')
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class Quiz(models.Model):
    """A quiz attached to a LearningCourse (one per course)."""
    course       = models.OneToOneField(LearningCourse, on_delete=models.CASCADE, related_name='quiz')
    title        = models.CharField(max_length=255)
    pass_percent = models.PositiveSmallIntegerField(default=60, help_text='Min % to pass')
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Quiz: {self.course.title}'

    def total_questions(self):
        return self.questions.count()


class QuizQuestion(models.Model):
    """A multiple-choice question inside a Quiz."""
    quiz        = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question    = models.TextField()
    option_a    = models.CharField(max_length=300)
    option_b    = models.CharField(max_length=300)
    option_c    = models.CharField(max_length=300)
    option_d    = models.CharField(max_length=300)
    answer      = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])
    explanation = models.TextField(blank=True)
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question[:80]

    def options(self):
        return {
            'A': self.option_a,
            'B': self.option_b,
            'C': self.option_c,
            'D': self.option_d,
        }


class CourseEnrollment(models.Model):
    """Tracks a student's enrollment in a LearningCourse."""
    student    = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='hub_enrollments')
    course     = models.ForeignKey(LearningCourse, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed  = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f'{self.student.user.username} → {self.course.title}'

    def progress_percent(self):
        total = self.course.lessons.filter(is_published=True).count()
        if not total:
            return 0
        done = LessonProgress.objects.filter(enrollment=self, completed=True).count()
        return int((done / total) * 100)


class LessonProgress(models.Model):
    """Marks a lesson as completed for a specific enrollment."""
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='lesson_progresses')
    lesson     = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progresses')
    completed  = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('enrollment', 'lesson')

    def __str__(self):
        return f'{self.enrollment} — {self.lesson.title}'


class QuizAttempt(models.Model):
    """Records a student's quiz attempt."""
    enrollment  = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='quiz_attempts')
    score       = models.PositiveSmallIntegerField(default=0)
    total       = models.PositiveSmallIntegerField(default=0)
    passed      = models.BooleanField(default=False)
    answers     = models.JSONField(default=dict, help_text='{"question_id": "A", ...}')
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        return f'{self.enrollment} — {self.score}/{self.total}'

    def percent(self):
        return int((self.score / self.total) * 100) if self.total else 0


class Certificate(models.Model):
    """Awarded when a student completes a course with a passing quiz score."""
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    enrollment     = models.OneToOneField(CourseEnrollment, on_delete=models.CASCADE, related_name='certificate')
    issued_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Certificate #{self.certificate_id} — {self.enrollment.course.title}'

    @property
    def student(self):
        return self.enrollment.student

    @property
    def course(self):
        return self.enrollment.course


# ── Legacy compatibility (old Course / CourseApplication) ──────────────────────
class Course(models.Model):
    """Legacy model kept so old migrations don't break."""
    from companies.models import Company as _Company
    title        = models.CharField(max_length=255)
    provider     = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    description  = models.TextField(blank=True)
    duration     = models.CharField(max_length=100, blank=True)
    level        = models.CharField(max_length=100, blank=True)
    mode         = models.CharField(max_length=50, default='Online')
    deadline     = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

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
    student    = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='course_applications')
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='applications')
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_course_application'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student.user.username} - {self.course.title}'
