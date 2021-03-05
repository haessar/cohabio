import os

import gpxpy.gpx
import pandas as pd
from tqdm import tqdm

from cohabio.settings import MEDIA_ROOT

london_data_dir = os.path.join(MEDIA_ROOT, 'mapper', 'city_data', 'london')

locations_path = os.path.join(london_data_dir, 'greater_london.gpx')
rail_usage_path = os.path.join(london_data_dir, 'Estimates-of-Station-Usage-in-2014-15.xlsx')
tube_usage_path = os.path.join(london_data_dir, 'multi-year-station-entry-and-exit-figures.xls')

usage = {
    'rail': {
        'path': rail_usage_path,
        'sheet': 'Estimates of Station Usage',
        'name_column': 'Station Name',
        'value_column': '1415 Entries & Exits'
    },
    'tube': {
        'path': tube_usage_path,
        'sheet': '2014 Entry & Exit',
        'name_column': 'Station',
        'value_column': 'million'
    }
}


def _remove_london(name):
    if name.startswith('London'):
        return name.split('London')[1].strip()
    return name


def _remove_whitespace(name):
    return ''.join(name.split(' '))


def _get_and_assign_usage(sheet, name_column, value_column, place):
    output = sheet[
                (sheet[name_column] == place.name) |
                (sheet[name_column] == _remove_london(place.name)) |
                (sheet[name_column] == _remove_whitespace(place.name))
            ]
    if len(output) == 1:
        place.usage = int(output[value_column])
        return True
    elif len(output) > 1:
        place.usage = output[value_column].sum(axis=0)


def _prepare_rail_usage_df(path):
    df = pd.read_excel(rail_usage_path, sheet_name=usage['rail']['sheet'])
    return df[df['Government Office Region (GOR)'] == 'London']


def _prepare_tube_usage_df(path):
    df = pd.read_excel(tube_usage_path, sheet_name=usage['tube']['sheet'], skiprows=6)
    # Remove NaN Station row
    df = df[pd.notnull(df[usage['tube']['name_column']])]
    # Remove bracketed terms in station name to ensure matching
    df[usage['tube']['name_column']] = df[usage['tube']['name_column']].apply(lambda x: x.split('(')[0].strip())
    # Convert from millions units
    df[usage['tube']['value_column']] = df[usage['tube']['value_column']].apply(lambda x: x * 1000000)
    return df


def add_london(model):
    gpx_file = open(locations_path, 'r')
    gpx = gpxpy.parse(gpx_file)
    rail = _prepare_rail_usage_df(rail_usage_path)
    tube = _prepare_tube_usage_df(tube_usage_path)

    # Delete GeoNames record for London
    try:
        model.objects.get(name='London', country_code='GB', source='geonames').delete()
    except Exception:
        pass

    for wp in tqdm(gpx.waypoints, total=len(gpx.waypoints), desc='London stations'):
        place, created = model.objects.get_or_create(
            name=wp.name,
            latitude=wp.latitude,
            longitude=wp.longitude,
            country_code='GB',
            source='london'
        )
        from_rail = _get_and_assign_usage(rail, usage['rail']['name_column'], usage['rail']['value_column'], place)
        if not from_rail:
            _get_and_assign_usage(tube, usage['tube']['name_column'], usage['tube']['value_column'], place)
        place.save()


def del_london(model):
    model.objects.filter(source="london").delete()
