from django.db import migrations
from tqdm import tqdm

from mapper.city_place_data import *


CITIES_TO_ADD = {
    'london': {'country': 'GB', 'verbose_name': 'London'},
    'washington_dc': {'country': 'US', 'verbose_name': 'London'},
    'glasgow': {'country': 'GB', 'verbose_name': 'Glasgow'},
}


def forwards_func(apps, schema_editor):
    PlaceData = apps.get_model("mapper", "PlaceData")
    db_alias = schema_editor.connection.alias

    for city, info in tqdm(CITIES_TO_ADD.items(), total=len(CITIES_TO_ADD), desc='Dump city data'):
        # Delete GeoNames record
        try:
            PlaceData.objects.get(name=info['verbose_name'], country_code=info['country'], source='geonames').delete()
        except Exception:
            pass

        for records in getattr(globals()[city], 'add_{}'.format(city))():
            PlaceData.objects.using(db_alias).bulk_create(
                PlaceData(**{**vals, 'source': city, 'country_code': info['country']}) for vals in records
            )


def reverse_func(apps, schema_editor):
    PlaceData = apps.get_model("mapper", "PlaceData")
    db_alias = schema_editor.connection.alias

    for city in CITIES_TO_ADD.keys():
        PlaceData.objects.using(db_alias).filter(source=city).delete()


class Migration(migrations.Migration):
    dependencies = [("mapper", "0002_dump_geonames")]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
