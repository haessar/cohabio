import os

from django.db import migrations
import pandas as pd

from cohabio.settings import MEDIA_ROOT
from cohabio.config import GEONAMES_FILENAME


def _get_table_columns_intersect(columns, model):
    field_names = set(f.name for f in model._meta.get_fields())
    return list(field_names.intersection(columns))


def forwards_func(apps, schema_editor):
    PlaceData = apps.get_model("mapper", "PlaceData")
    db_alias = schema_editor.connection.alias

    cities_path = os.path.join(MEDIA_ROOT, 'mapper', 'city_data', GEONAMES_FILENAME)

    # Column names from city_data/readme.txt
    cols = [
        'geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude', 'feature_class', 'feature_code',
        'country_code', 'cc2', 'admin1_code', 'admin2_code', 'admin3_code', 'admin4_code', 'population', 'elevation',
        'dem', 'timezone', 'modification_date'
    ]

    cities = pd.read_csv(cities_path, sep='\t', names=cols, encoding='utf-8', low_memory=False)
    cities = cities.sort_values(by=['population'], ascending=False).reset_index(drop=True)
    cities['name'] = cities['asciiname']
    cities = cities[_get_table_columns_intersect(cols, PlaceData)]
    cities['source'] = 'geonames'

    PlaceData.objects.using(db_alias).bulk_create(
        PlaceData(**vals) for vals in cities.to_dict('records')
    )


def reverse_func(apps, schema_editor):
    PlaceData = apps.get_model("mapper", "PlaceData")
    db_alias = schema_editor.connection.alias

    PlaceData.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):
    dependencies = [("mapper", "0001_initial")]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
