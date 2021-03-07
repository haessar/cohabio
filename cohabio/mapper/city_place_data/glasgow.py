import os

from convertbng.util import convert_lonlat
import pandas as pd
from tqdm import tqdm

from cohabio.settings import MEDIA_ROOT

glasgow_data_dir = os.path.join(MEDIA_ROOT, 'mapper', 'city_data', 'glasgow')

subways_path = os.path.join(glasgow_data_dir, 'glasgow-subway-station-locations.csv')
rail_path = os.path.join(glasgow_data_dir, 'glw-railreferences.csv')


def add_glasgow(model):
    tube = pd.read_csv(subways_path)
    tube = tube[pd.notnull(tube['Station Name'])]

    rail = pd.read_csv(rail_path)
    rail = rail.rename(columns={'StationName': 'Station Name'})
    rail['Station Name'] = rail['Station Name'].str.replace(r'Rail Station', '')

    stations = pd.concat([tube, rail], ignore_index=True)
    lon, lat = convert_lonlat(stations['Easting'].to_list(), stations['Northing'].to_list())
    stations['lon'] = lon
    stations['lat'] = lat

    # Delete GeoNames record for Glasgow
    try:
        model.objects.get(name='Glasgow', country_code='GB', source='geonames').delete()
    except Exception:
        pass

    for idx, station in tqdm(stations.iterrows(), total=len(stations), desc='Glasgow stations'):
        place, created = model.objects.get_or_create(
            name=station['Station Name'],
            latitude=station['lat'],
            longitude=station['lon'],
            country_code='GB',
            source='glasgow'
        )
        place.save()


def del_glasgow(model):
    model.objects.filter(source="glasgow").delete()
