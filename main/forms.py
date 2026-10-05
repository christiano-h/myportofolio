from django.forms import (
    DateTimeField,
    DateTimeInput,
    ModelForm,
    Select,
    Textarea,
    TextInput,
    URLInput,
)
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from main.models import Experience, Project


class ExperienceForm(ModelForm):
    # dideklarasikan eksplisit agar input_formats cocok dengan <input type="datetime-local">
    ended_at = DateTimeField(
        required=False,
        label="Tanggal Selesai",
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
            "title": "Nama Experience",
            "job_title": "Jabatan",
            "category": "Kategori",
            "thumbnail": "Thumbnail", #link
            "summary": "Ringkasan", 
            "content": "Konten",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Contoh: RISTEK Fasilkom UI",
                    "maxlength": 100,
                }
            ),
            "job_title": TextInput(
                attrs={
                    "placeholder": "Contoh: Project Officer",
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
    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError("Nama experience tidak boleh hanya berisi tag HTML.")
        return title

    def clean_job_title(self):
        return strip_tags(self.cleaned_data["job_title"] or "").strip()

    def clean_summary(self):
        return strip_tags(self.cleaned_data["summary"] or "").strip()

    def clean_content(self):
        return strip_tags(self.cleaned_data["content"] or "").strip()



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

    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError("Nama proyek tidak boleh hanya berisi tag HTML.")
        return title

    def clean_tech_stack(self):
        # `or ""` penting: field ini Optional (bisa None di instance lama),
        # sedangkan strip_tags(None) melempar TypeError.
        return strip_tags(self.cleaned_data["tech_stack"] or "").strip()

    def clean_content(self):
        return strip_tags(self.cleaned_data["content"] or "").strip()

    def clean_description(self):
        return strip_tags(self.cleaned_data["description"] or "").strip()

