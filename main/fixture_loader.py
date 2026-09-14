import json
from pathlib import Path

from django.conf import settings

FIXTURE_DIR = Path(settings.BASE_DIR) / "main" / "fixtures"

def seed_fixture(apps, schema_editor=None, fixture="initial_data.json", app_label="main", timpa=True):
    path = FIXTURE_DIR / fixture
    data = json.loads(path.read_text(encoding="utf-8"))
    jumlah = 0

    for entry in data:
        if not entry["model"].startswith(app_label + "."):
            continue

        model = apps.get_model(entry["model"])
        fields = dict(entry["fields"])
        
        started_at = fields.pop("started_at", None)

        pk = entry["pk"]
        if timpa:
            obj, _ = model.objects.update_or_create(id=pk, defaults=fields)
        else:
            obj, _ = model.objects.get_or_create(id=pk, defaults=fields)

        if started_at is not None:
            model.objects.filter(pk=obj.pk).update(started_at=started_at)

        jumlah += 1

    return jumlah
