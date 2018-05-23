"""
Run in the following way:

1) Start a django shell: 'python manage.py shell'
2) Import this script within shell with: 'import mapper.add_to_db.master_cities'
*) Can set up Pycharm config to debug the django shell (repeat step 2 while debugging)
"""

import os

import pandas as pd
from tqdm import tqdm

# from mapper.add_to_db.dc import dc_data
# from mapper.add_to_db.london import london_data

from mapper.models import PlaceData
from cohabio.settings import BASE_DIR

cities_path = os.path.join(BASE_DIR, 'media', 'mapper', 'city_data', 'cities5000.txt')

def get_table_columns_intersect(columns, model):
    field_names = set(f.name for f in model._meta.get_fields())
    return list(field_names.intersection(columns))


# Process global cities data.

# Column names from city_data/readme.txt
cols = [
    'geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude', 'feature_class', 'feature_code',
    'country_code', 'cc2', 'admin1_code', 'admin2_code', 'admin3_code', 'admin4_code', 'population', 'elevation',
    'dem', 'timezone', 'modification_date'
]
cities = pd.read_csv(cities_path, sep='\t', names=cols, encoding='utf-8', low_memory=False)
cities = cities.sort_values(by=['population'], ascending=False).reset_index(drop=True)
cities['name'] = cities['asciiname']
cities = cities[get_table_columns_intersect(cols, PlaceData)]
for idx, city in tqdm(cities.iterrows(), total=len(cities), desc='Global cities (population > 5000)'):
    place, created = PlaceData.objects.get_or_create(**city)
    if created:
        try:
            place.save()
        except Exception as e:
            tqdm.write(e)
            tqdm.write('Unable to save {} ({}) to database.'.format(place.city.name, city.country_code))

# Process specific cities data.

# TODO Fix london.py
# london_data(PlaceData)
# dc_data(PlaceData)
