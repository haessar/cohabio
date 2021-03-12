import os

from convertbng.util import convert_lonlat
import pandas as pd

from cohabio.settings import MEDIA_ROOT

glasgow_data_dir = os.path.join(MEDIA_ROOT, 'mapper', 'city_data', 'glasgow')

subways_path = os.path.join(glasgow_data_dir, 'glasgow-subway-station-locations.csv')
rail_path = os.path.join(glasgow_data_dir, 'glw-railreferences.csv')
datazones_path = os.path.join(glasgow_data_dir, 'b50723180f1742b480ff94b11c445638datazonewitheastingsandnorthings.csv')

cols = ['name', 'latitude', 'longitude']


def add_glasgow():
    tube = pd.read_csv(subways_path)
    tube = tube[pd.notnull(tube['Station Name'])]
    tube = tube.rename(columns={'Station Name': 'name'})

    rail = pd.read_csv(rail_path)
    rail = rail.rename(columns={'StationName': 'name'})
    # Remove prefix "Rail Station" from each name.
    rail['name'] = rail['name'].str.replace(r'Rail Station', '')

    stations = pd.concat([tube, rail], ignore_index=True)
    lon, lat = convert_lonlat(stations['Easting'].to_list(), stations['Northing'].to_list())
    stations['longitude'] = lon
    stations['latitude'] = lat

    yield stations[cols].to_dict('records')

    datazones = pd.read_csv(datazones_path)
    # Multiple rows share the same name but different coordinates, so group-by and take the mean.
    datazones = datazones.groupby(by="Intermediate Geography Name").mean()
    datazones['name'] = datazones.index
    datazones = datazones.rename(columns={'Longitude': 'longitude', 'Latitude': 'latitude'})

    yield datazones[cols].to_dict('records')
