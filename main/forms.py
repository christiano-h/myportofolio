from django.forms import (
    DateTimeField,
    DateTimeInput,
    ModelForm,
    Select,
    Textarea,
    TextInput,
    URLInput,
)

from main.models import Experience, Project


class ExperienceForm(ModelForm):
    # dideklarasikan eksplisit agar input_formats cocok dengan <input type="datetime-local">
    ended_at = DateTimeField(
        required=False,
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
        widget=DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )

    class Meta:
        model = Experience
        # started_at tidak disertakan karena auto_now_add=True (editable=False)
        fields = [
            "title",
            "job_title",
            "category",
            "thumbnail",
            "summary",
            "content",
            "ended_at",
        ]

        labels = {
            "title": "Nama Proyek",
            "job_title": "Jabatan",
            "category": "Kategori",
            "thumbnail": "Thumbnail", #link
            "summary": "Ringkasan", 
            "content": "Konten",
            "ended_at": "Tanggal Selesai",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Portfolio Website",
                    "maxlength": 100,
                }
            ),
            "job_title": TextInput(
                attrs={
                    "placeholder": "Contoh: Software Engineer",
                    "maxlength": 100,
                }
            ),
            "category": Select(
                choices=Experience.EXPERIENCE_CHOICES,
                attrs={
                    "class": "form-select",
                },
            ),
            "thumbnail": URLInput(
                attrs={
                    "placeholder": "https://example.com/thumbnail.jpg",
                }
            ),
            "summary": Textarea(
                attrs={
                    "placeholder": "Ringkasan pengalaman (teks pendek di kartu)",
                    "rows": 3,
                }
            ),
            "content": Textarea(
                attrs={
                    "placeholder": "Isi lengkap halaman detail",
                    "rows": 5,
                }
            ),
        }


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = [
            "title",
            "tech_stack",
            "thumbnail",
            "project_url",
            "description",
            "content",
        ]

        labels = {
            "title": "Nama Proyek",
            "tech_stack": "Tech Stack",
            "thumbnail": "Thumbnail",
            "project_url": "Link Project",
            "description": "Deskripsi",
            "content": "Konten",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Portfolio Website",
                    "maxlength": 100,
                }
            ),
            "tech_stack": TextInput(
                attrs={
                    "placeholder": "Contoh: Django, PostgreSQL, Bootstrap",
                    "maxlength": 200,
                }
            ),
            "thumbnail": URLInput(
                attrs={
                    "placeholder": "https://example.com/thumbnail.jpg",
                }
            ),
            "project_url": URLInput(
                attrs={
                    "placeholder": "Contoh: https://github.com/christiano-h/portfolio",
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Ringkasan proyek (teks pendek di kartu)",
                    "rows": 3,
                }
            ),
            "content": Textarea(
                attrs={
                    "placeholder": "Isi lengkap halaman detail",
                    "rows": 5,
                }
            ),
        }
