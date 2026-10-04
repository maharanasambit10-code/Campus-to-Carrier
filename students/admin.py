from django.contrib import admin
from django.utils.html import format_html
from .models import Achievement, Certification, Internship, Project, StudentProfile, Skill, StudentSkill


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'college', 'graduation_year', 'profile_photo_preview')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department', 'college')
    list_filter = ('department', 'graduation_year')

    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:50%;" />',
                obj.profile_photo.url,
            )
        return 'No photo'

    profile_photo_preview.short_description = 'Photo'


admin.site.register(Skill)
admin.site.register(StudentSkill)
admin.site.register(Project)
admin.site.register(Certification)
admin.site.register(Internship)
admin.site.register(Achievement)