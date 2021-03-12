from django.db import migrations
from tqdm import tqdm

from mapper.city_place_data import *


CITIES_TO_ADD = {
    'london': 'GB',
    'washington_dc': 'US',
    'glasgow': 'GB',
}


def forwards_func(apps, schema_editor):
    PlaceData = apps.get_model("mapper", "PlaceData")
    db_alias = schema_editor.connection.alias

    for city, country in tqdm(CITIES_TO_ADD.items(), total=len(CITIES_TO_ADD), desc='Dump city data'):
        for records in getattr(globals()[city], 'add_{}'.format(city))(PlaceData):
            PlaceData.objects.using(db_alias).bulk_create(
                PlaceData(**{**vals, 'source': city, 'country_code': country}) for vals in records
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
