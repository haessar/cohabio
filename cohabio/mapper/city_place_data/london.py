import os

import gpxpy.gpx
import pandas as pd

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


def _get_and_assign_usage(df, ref_df, name_column, value_column, apply_funcs=(_remove_london, _remove_whitespace)):
    """
    Vectorized method to merge 'usage' values from a ref_df after applying a sequence of apply_funcs to the df 'name'
    column. These apply_funcs allow us to slightly alter the station name to retest for a match in ref_df.
    e.g. df might have a name value of 'London Waterloo' corresponding to ref_df's 'Waterloo',
     so apply_funcs=(_remove_london,) will remove any 'London' prefix from df.name and result in a match.
    :param df: DataFrame into which 'usage' values should inserted.
    :param ref_df: Reference DataFrame from which to acquire 'usage' values.
    :param name_column: ref_df column name corresponding to station names.
    :param value_column: ref_df column name corresponding to 'usage' values.
    :param apply_funcs: tuple of str manipulation functions to apply to df.name.
    :return: df with additional 'usage' column.
    """
    if 'usage' in df:
        del df['usage']
    cols = list(df.columns)
    df = df.merge(ref_df[[name_column, value_column]], left_on='name', right_on=name_column, how='left')
    df = df.rename(columns={value_column: 'usage'})

    for f in apply_funcs:
        df['name' + f.__name__] = df.name.apply(f)
        df = df.merge(ref_df[[name_column, value_column]], left_on='name' + f.__name__, right_on=name_column,
                      how='left')
        df['usage'] = df['usage'].where(df['usage'].notnull(), df[value_column])
        df = df.drop(value_column, axis=1)

    return df[cols + ['usage']]


def _prepare_rail_usage_df(path):
    df = pd.read_excel(path, sheet_name=usage['rail']['sheet'])
    df[usage['rail']['value_column']] = df[usage['rail']['value_column']]
    return df[df['Government Office Region (GOR)'] == 'London']


def _prepare_tube_usage_df(path):
    df = pd.read_excel(path, sheet_name=usage['tube']['sheet'], skiprows=6)
    # Remove NaN Station row
    df = df[pd.notnull(df[usage['tube']['name_column']])]
    # Remove bracketed terms in station name to ensure matching
    df[usage['tube']['name_column']] = df[usage['tube']['name_column']].apply(lambda x: x.split('(')[0].strip())
    # Convert from millions units
    df[usage['tube']['value_column']] = df[usage['tube']['value_column']].apply(lambda x: x * 1000000)
    return df.sort_values('million', ascending=False).drop_duplicates('Station')


def add_london():
    gpx_file = open(locations_path, 'r')
    gpx = gpxpy.parse(gpx_file)
    rail = _prepare_rail_usage_df(rail_usage_path)
    tube = _prepare_tube_usage_df(tube_usage_path)

    records = [{'name': wp.name,
          'latitude': wp.latitude,
          'longitude': wp.longitude} for wp in gpx.waypoints]
    df = pd.DataFrame(records).drop_duplicates('name')
    df = _get_and_assign_usage(df, rail, usage['rail']['name_column'], usage['rail']['value_column'])
    # Any usage values missing from rail DataFrame, try to obtain from tube DataFrame.
    df_no_usage = df[pd.isnull(df['usage'])]
    df_rail_usage = df[df['usage'].notnull()]
    df_tube_usage = _get_and_assign_usage(
        df_no_usage, tube, usage['tube']['name_column'], usage['tube']['value_column']
    )
    df = pd.concat([df_rail_usage, df_tube_usage]).sort_index()

    yield df.to_dict('records')
