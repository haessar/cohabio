from django.db import migrations

from mapper.city_place_data import *


CITIES_TO_ADD = [
    'london',
    'dc',
    'glasgow',
]


def forwards_func(apps, schema_editor):
    PlaceData = apps.get_model("mapper", "PlaceData")

    for city in CITIES_TO_ADD:
        getattr(globals()[city], 'add_{}'.format(city))(PlaceData)


def reverse_func(apps, schema_editor):
    PlaceData = apps.get_model("mapper", "PlaceData")

    for city in CITIES_TO_ADD:
        getattr(globals()[city], 'del_{}'.format(city))(PlaceData)


class Migration(migrations.Migration):
    dependencies = [("mapper", "0002_dump_geonames")]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
