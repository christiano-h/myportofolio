from django.db import migrations

from main.fixture_loader import seed_fixture


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0006_sync_fixture_experience"),
    ]

    operations = [
        migrations.RunPython(seed_fixture, migrations.RunPython.noop),
    ]
