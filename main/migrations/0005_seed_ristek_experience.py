from django.db import migrations

RISTEK_PK = "3d668088-5f05-4ef3-8c97-80698d29bcf5"
RISTEK_TITLE = "RISTEK Fasilkom UI"
RISTEK_TEXT = "Haiii guys!!! PEKAN RISTEK kan sebentar lagi, jangan lupa untuk daftar Open Class BGP YAAA <3"

RISTEK_FIELDS = {
    "title": RISTEK_TITLE,
    "job_title": "Business Growth & Partnerships Associate",
    "category": "volunteer",
    "thumbnail": "/static/css/img/ristek.jpg",
    "summary": RISTEK_TEXT,
    "content": RISTEK_TEXT,
}

SUMMARY_BARU = {
    "Spiritual Retreat SMAN 1 Jakarta": "Hai disini aku jadi Ketua Retreat di SMAN 1 Jakarta, pasti Micguel Katili tidak expect yeahhh",
    "SELARAS 5.0": "Jadi PDD di SELARAS 5.0, disini ngedokum banyak artis yey, tapi gak bagus-bagus amat ah, kalah sama SMAN 68 yang ngundang Tulus itu",
    "MPK SMAN 1 Jakarta": "Ahh finally something good, jadi Komisi Audit di MPK SMAN 1 Jakarta, cape banget double job :(",
    "Open House Fasilkom UI": "Ini adalah akhir dari dunia PDD di hidupku, tadinya. Tapi ada Mbak Tiffany yang mecut buat jadi SINTAKS. TOLONGGGG!!!",
}


def seed(apps, schema_editor):
    Experience = apps.get_model("main", "Experience")
    exp = Experience.objects.filter(pk=RISTEK_PK).first()
    if exp is None:
        exp = Experience.objects.filter(title=RISTEK_TITLE).first()
    if exp is None:
        Experience.objects.create(id=RISTEK_PK, **RISTEK_FIELDS)
    else:
        for field, value in RISTEK_FIELDS.items():
            setattr(exp, field, value)
        exp.save()
    for title, summary in SUMMARY_BARU.items():
        Experience.objects.filter(title=title).update(summary=summary)


def unseed(apps, schema_editor):
    Experience = apps.get_model("main", "Experience")
    Experience.objects.filter(title=RISTEK_TITLE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0004_project_content"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
