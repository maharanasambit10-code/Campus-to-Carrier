from django.contrib import admin
from .models import (
    LearningCourse, Lesson, Quiz, QuizQuestion,
    CourseEnrollment, LessonProgress, QuizAttempt, Certificate,
    Course, CourseApplication,
)


@admin.register(LearningCourse)
class LearningCourseAdmin(admin.ModelAdmin):
    list_display  = ('title', 'category', 'level', 'duration_hrs', 'is_published', 'order')
    list_filter   = ('category', 'level', 'is_published')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order',)


class LessonInline(admin.TabularInline):
    model  = Lesson
    extra  = 1
    fields = ('order', 'title', 'content_type', 'duration_min', 'is_published')


class QuizInline(admin.StackedInline):
    model = Quiz
    extra = 0


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display  = ('title', 'course', 'order', 'content_type', 'duration_min', 'is_published')
    list_filter   = ('content_type', 'is_published', 'course')
    search_fields = ('title', 'course__title')
    ordering      = ('course', 'order')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'pass_percent', 'total_questions')


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display  = ('question', 'quiz', 'answer', 'order')
    list_filter   = ('quiz', 'answer')
    search_fields = ('question',)
    ordering      = ('quiz', 'order')


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'completed')
    list_filter  = ('completed', 'course')
    search_fields = ('student__user__username', 'course__title')


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'completed', 'completed_at')
    list_filter  = ('completed',)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'score', 'total', 'passed', 'attempted_at')
    list_filter  = ('passed',)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'enrollment', 'issued_at')
    readonly_fields = ('certificate_id', 'issued_at')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'is_published', 'created_at')


@admin.register(CourseApplication)
class CourseApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'created_at')
    list_filter  = ('status',)
