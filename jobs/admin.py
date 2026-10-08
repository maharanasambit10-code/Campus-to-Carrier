from django.contrib import admin
from django.utils.html import format_html
from .models import Job, SavedJob


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_logo', 'company', 'job_type', 'work_mode', 'salary', 'location', 'application_deadline', 'is_active', 'is_verified')
    list_filter = ('job_type', 'work_mode', 'is_active', 'is_verified', 'company__company_type', 'created_at')
    search_fields = ('title', 'company__name', 'location', 'description', 'required_programming_languages', 'required_frameworks', 'required_technologies', 'qualifications')
    list_editable = ('is_active', 'is_verified')
    filter_horizontal = ('required_skills', 'preferred_skills')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Role Overview', {
            'fields': ('title', 'company', 'description', 'job_type', 'work_mode', 'internship_type', 'is_active', 'is_verified')
        }),
        ('Compensation & Location', {
            'fields': ('salary', 'location')
        }),
        ('Qualifications & Eligibility Criteria', {
            'fields': ('qualifications', 'eligible_degree', 'minimum_cgpa', 'maximum_backlogs', 'graduation_year', 'allowed_departments', 'min_tenth', 'min_twelfth', 'experience_required', 'experience_text')
        }),
        ('Technical Skills Required', {
            'fields': ('required_skills', 'preferred_skills', 'required_programming_languages', 'required_frameworks', 'required_technologies'),
            'description': 'Select skills from the Skill database or enter comma-separated languages/frameworks.'
        }),
        ('Application Schedule', {
            'fields': ('application_deadline',)
        }),
    )

    def company_logo(self, obj):
        url = obj.company.get_logo_url
        if url:
            return format_html(
                '<img src="{}" style="width: 28px; height: 28px; object-fit: contain; border-radius: 6px; background: #fff; border: 1px solid #e2e8f0; padding: 2px;" alt="{}" />',
                url, obj.company.name
            )
        return format_html('<span>{}</span>', obj.company.initials)
    company_logo.short_description = "Logo"


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('student', 'job', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('student__user__username', 'student__user__first_name', 'job__title', 'job__company__name')