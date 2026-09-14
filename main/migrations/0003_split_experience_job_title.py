from django.db import migrations

SEPARATOR = " — "


def split_job_title(apps, schema_editor):
    # "Jabatan — Nama Kegiatan" -> job_title="Jabatan", title="Nama Kegiatan"
    Experience = apps.get_model("main", "Experience")
    for experience in Experience.objects.all():
        if experience.job_title or SEPARATOR not in experience.title:
            continue
        job_title, _, event_title = experience.title.partition(SEPARATOR)
        experience.job_title = job_title.strip()
        experience.title = event_title.strip()
        experience.save(update_fields=["job_title", "title"])


def join_job_title(apps, schema_editor):
    # kebalikannya: gabungkan kembali job_title + title menjadi satu title
    Experience = apps.get_model("main", "Experience")
    for experience in Experience.objects.exclude(job_title__isnull=True).exclude(job_title=""):
        experience.title = "%s%s%s" % (experience.job_title, SEPARATOR, experience.title)
        experience.job_title = None
        experience.save(update_fields=["job_title", "title"])


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_experience_job_title"),
    ]

    operations = [
        migrations.RunPython(split_job_title, join_job_title),
    ]
