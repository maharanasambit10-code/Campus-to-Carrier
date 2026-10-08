from django.contrib import admin
from django.utils.html import format_html
from .models import Company, CompanyConnection
from jobs.models import Job


class JobInline(admin.TabularInline):
    model = Job
    extra = 0
    fields = ('title', 'job_type', 'salary', 'location', 'application_deadline', 'is_active', 'is_verified')
    show_change_link = True


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('logo_preview', 'name', 'company_type', 'industry', 'headquarters', 'verification_status', 'open_positions', 'internship_opportunities', 'created_at')
    list_filter = ('company_type', 'verification_status', 'industry')
    search_fields = ('name', 'industry', 'description', 'locations', 'tech_stack', 'headquarters')
    list_editable = ('verification_status', 'open_positions', 'internship_opportunities')
    inlines = [JobInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'tagline', 'description', 'industry', 'company_type', 'verification_status')
        }),
        ('Brand & Logo Assets', {
            'fields': ('logo', 'logo_url', 'website'),
            'description': 'Upload a company logo file or provide an official SVG/CDN logo URL.'
        }),
        ('Location & Team Scale', {
            'fields': ('headquarters', 'locations', 'employee_count', 'funding_stage')
        }),
        ('Technical Stack & Hiring Process', {
            'fields': ('tech_stack', 'hiring_process')
        }),
        ('Opportunity Counters', {
            'fields': ('open_positions', 'internship_opportunities', 'is_demo')
        }),
    )

    def logo_preview(self, obj):
        url = obj.get_logo_url
        if url:
            return format_html(
                '<img src="{}" style="width: 32px; height: 32px; object-fit: contain; border-radius: 6px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 2px;" alt="{}" />',
                url, obj.name
            )
        return format_html('<span style="font-weight: bold; color: #64748b;">{}</span>', obj.initials)
    logo_preview.short_description = "Logo"


@admin.register(CompanyConnection)
class CompanyConnectionAdmin(admin.ModelAdmin):
    list_display = ('student', 'company', 'preferred_role', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('student__user__username', 'student__user__first_name', 'student__user__last_name', 'company__name', 'preferred_role')