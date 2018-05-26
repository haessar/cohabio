import datetime
import pytz

from .deploy_probes import probe_gps_intersect
from .prepare_markers import sorter
from ..models import UserInfo

def compare_users(locations, modes, times, geolocator):
    """
    Ties everything together.
    """
    dat, entry_count = probe_gps_intersect(locations, modes, times, geolocator)
    tz = pytz.timezone('UTC')
    ui = UserInfo(
        entries=entry_count, time_stamp=datetime.datetime.now(tz),
        work1=locations[0], work2=locations[1],
        trans1=modes[0], trans2=modes[1],
        mcom1=times[0], mcom2=times[1],
        results=len(dat) if isinstance(dat, dict) else 0
    )
    ui.save()
    if isinstance(dat, str):
        return dat
    return sorter(dat, 0.2)
