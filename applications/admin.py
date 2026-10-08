from django.contrib import admin
from django.utils.html import format_html
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate_name', 'job_title', 'company_name', 'status', 'match_percentage', 'resume_score', 'resume_link', 'created_at')
    list_filter = ('status', 'job__job_type', 'created_at', 'experience_level')
    search_fields = ('full_name', 'email', 'phone', 'college', 'job__title', 'job__company__name', 'student__user__username')
    list_editable = ('status',)
    date_hierarchy = 'created_at'

    actions = ['mark_shortlisted', 'mark_interview', 'mark_selected', 'mark_rejected']

    def candidate_name(self, obj):
        return obj.full_name or obj.student.user.get_full_name() or obj.student.user.username
    candidate_name.short_description = "Candidate"

    def job_title(self, obj):
        return obj.job.title
    job_title.short_description = "Job Role"

    def company_name(self, obj):
        return obj.job.company.name
    company_name.short_description = "Company"

    def resume_link(self, obj):
        resume_file = obj.custom_resume or getattr(obj.student, 'resume', None)
        if resume_file:
            return format_html('<a href="{}" target="_blank" style="font-weight: 600; color: #2563eb;">📄 View Resume</a>', resume_file.url)
        return format_html('<span style="color: #94a3b8;">No File</span>')
    resume_link.short_description = "Resume"

    def mark_shortlisted(self, request, queryset):
        queryset.update(status='SHORTLISTED')
    mark_shortlisted.short_description = "Mark selected as Shortlisted"

    def mark_interview(self, request, queryset):
        queryset.update(status='INTERVIEW')
    mark_interview.short_description = "Schedule Interview for selected"

    def mark_selected(self, request, queryset):
        queryset.update(status='SELECTED')
    mark_selected.short_description = "Mark selected as Selected / Offer Given"

    def mark_rejected(self, request, queryset):
        queryset.update(status='REJECTED')
    mark_rejected.short_description = "Mark selected as Rejected"