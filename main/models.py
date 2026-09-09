import uuid
from django.db import models


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
    category = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='full-time')
    # Foto/SVG untuk gambar kartu (path static absolut /static/css/img/... atau URL eksternal)
    thumbnail = models.URLField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)   # teks pendek di kartu
    content = models.TextField(blank=True, null=True)   # isi blog halaman detail
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    @property
    def is_ongoing(self):
        return self.ended_at is None
