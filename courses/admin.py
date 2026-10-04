from django.contrib import admin

from .models import Course, CourseApplication


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'mode', 'deadline', 'is_published', 'created_at')
    list_filter = ('is_published', 'mode')
    search_fields = ('title', 'provider__name')


@admin.register(CourseApplication)
class CourseApplicationAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('course__title', 'student__user__username', 'student__user__email')
