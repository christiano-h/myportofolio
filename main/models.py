import uuid
from django.db import models
from django.contrib.auth.models import User


class Experience(models.Model):
    EXPERIENCE_CHOICES = [
        ('internship', 'Internship'),
        ('research', 'Research'),
        ('volunteer', 'Volunteer'),
        ('part-time', 'Part-Time'),
        ('full-time', 'Full-Time'),
        ('freelance', 'Freelance'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='full-time')
    thumbnail = models.URLField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)   # teks pendek di kartu
    content = models.TextField(blank=True, null=True)   # isi blog halaman detail
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    starred_by = models.ManyToManyField(
        User, related_name="starred_experiences", blank=True
    )

    def __str__(self):
        if self.job_title:
            return self.job_title + ' — ' + self.title
        return self.title

    @property
    def is_ongoing(self):
        return self.ended_at is None


class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.URLField(blank=True, null=True)   # /static/css/img/... atau URL
    tech_stack = models.CharField(max_length=200, blank=True, null=True)   # teks bebas, mis. "Django, PostgreSQL"
    project_url = models.URLField(blank=True, null=True)   # link demo/repo
    content = models.TextField(blank=True, null=True)   # isi blog halaman detail
    starred_by = models.ManyToManyField(
        User, related_name="starred_projects", blank=True
    )
    
    @property
    def project_image_url(self):
        return self.thumbnail

    def __str__(self):
        return self.title
