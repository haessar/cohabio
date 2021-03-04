from datetime import datetime, timedelta
import pytz
import requests
import time
import urllib

from django.db.models import Sum
from ..models import UserInfo

from mapper.models import UserInfo
from mapper.functions.google_API import gmaps_client


def next_week_day(origin):
    """
    Returns the next weekday 9:00am as a datetime object for use in the distance_matrix arrival_time argument.
    """
    today = datetime.today()
    response = gmaps_client.timezone(timestamp=int(time.time()), location=(origin.latitude, origin.longitude))
    if response:
        offset = (response.get('dstOffset') + response.get('rawOffset')) / 60 ** 2  # UTC offset time in hours
        if today.weekday() < 4:  # Monday-Thursday
            next = today + timedelta(days=1)
        elif today.weekday() >= 4:  # Friday-Sunday
            next = today + timedelta(days=7 - today.weekday())
        return datetime(next.year, next.month, next.day, int(9 + offset))
    else:
        return datetime(today.year, today.month, today.day, 9)


def request_counter():
    """
    Function that finds total number of entries made today by querying database
    """
    tz = pytz.timezone('US/Pacific')
    pt = datetime.now(tz)
    pt_start = pt.replace(hour=12, minute=0, second=1, microsecond=0)
    pt_end = pt.replace(hour=11, minute=59, second=59, microsecond=0)
    if pt.hour >= 12:
        pt_end = pt_end + timedelta(days=1)
    else:
        pt_start = pt_start - timedelta(days=1)
    utc_tz = pytz.timezone('UTC')
    utc_start = pt_start.astimezone(utc_tz)
    utc_end = pt_end.astimezone(utc_tz)
    query = UserInfo.objects.filter(time_stamp__gte=utc_start).exclude(time_stamp__gte=utc_end)
    return query.aggregate(Sum('entries')).get('entries__sum', 0) or 0
