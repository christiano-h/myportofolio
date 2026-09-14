from django.contrib import admin
from main.models import Experience, Project


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('title', 'job_title', 'category', 'is_ongoing')
    search_fields = ('title', 'job_title')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')
