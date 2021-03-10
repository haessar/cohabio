from datetime import datetime, timedelta
from dateutil import tz
import time

from django.db.models import Sum

from mapper.models import SearchResults
from mapper.googlemaps_client import gmaps_client


def next_week_day(latitude, longitude):
    """
    Returns the next weekday 9:00am as a datetime object for use in the distance_matrix arrival_time argument.
    """
    today = datetime.today()
    response = gmaps_client.timezone(timestamp=int(time.time()), location=(latitude, longitude))
    if response:
        offset = (response.get('dstOffset') + response.get('rawOffset')) / 60 ** 2  # UTC offset time in hours
        if today.weekday() < 4:  # Monday-Thursday
            next = today + timedelta(days=1)
        elif today.weekday() >= 4:  # Friday-Sunday
            next = today + timedelta(days=7 - today.weekday())
        return datetime(next.year, next.month, next.day, int(9 + offset))
    else:
        return datetime(today.year, today.month, today.day, 9)


def daily_elements():
    """
    Function that finds total number of elements accrued today by querying database.

    "Your free daily request pool is reset at 12:00 am Pacific Time."
    from https://developers.google.com/maps/premium/usage-limits#maps-javascript-api-services-client-side
    """
    pt_tz = tz.gettz('US/Pacific')
    today = datetime.now(pt_tz).date()
    start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=pt_tz)

    utc_tz = tz.UTC
    utc_start = start.astimezone(utc_tz)
    utc_end = utc_start + timedelta(1)
    query = SearchResults.objects.filter(time_stamp__gte=utc_start).exclude(time_stamp__gte=utc_end)
    sum_elements = query.aggregate(Sum('you__elements'), Sum('them__elements')).values()
    return sum(sum_elements) if any(sum_elements) else 0
