from django.utils.html import strip_tags
from rest_framework import serializers

from main.models import Experience, Project


class ProjectSerializer(serializers.ModelSerializer):
    project_image_url = serializers.URLField(source="thumbnail", required=False, allow_blank=True, allow_null=True)
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "title", "description", "tech_stack",
            "project_url", "project_image_url", "content",
            "star_count", "is_starred", "starred_by_names",
        ]
        read_only_fields = ["id"]

    def validate_title(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_description(self, value):
        return strip_tags(value or "")

    def validate_tech_stack(self, value):
        return strip_tags(value or "")

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user in obj.starred_by.all()

    def get_starred_by_names(self, obj):
        return ", ".join(user.username for user in obj.starred_by.all())

    def validate_content(self, value):
        return strip_tags(value or "")


class ExperienceSerializer(ProjectSerializer):
    project_image_url = None

    class Meta:
        model = Experience
        fields = [
            "id", "title", "job_title", "category", "thumbnail", "summary",
            "content", "started_at", "ended_at", "is_ongoing",
            "star_count", "is_starred", "starred_by_names",
        ]
        read_only_fields = ["id", "started_at", "is_ongoing"]

    def validate_job_title(self, value):
        return strip_tags(value or "").strip()

    def validate_summary(self, value):
        return strip_tags(value or "").strip()
