import time

from geopy.exc import GeocoderQuotaExceeded, GeocoderTimedOut
from geopy.geocoders import GoogleV3
import numpy as np

from cohabio.local_config import GOOGLE_KEY


def deg_from_km_sq(d):
    """
    Crude formula to convert d kms to degrees of latitude/longitude.
    Use with caution near poles/equator!
    """
    km = 0.0089982311916
    return d * km


class GeoLocator(GoogleV3):
    api_key = GOOGLE_KEY

    def __init__(self, logger):
        super(GeoLocator, self).__init__(api_key=self.api_key)
        self.logger = logger
    def return_gps_from_place_names(self, listofplaces):
        listofcoords = []
        for item in listofplaces:
            while True:
                try:
                    gps = self.geocode(item)
                    break
                except (GeocoderTimedOut, GeocoderQuotaExceeded):
                    self.logger.warning('Failed to geocode. Sleeping')
                    time.sleep(5)
            if len(listofplaces) == 1:
                return gps
            else:
                listofcoords.append(gps)
        return listofcoords
    def average_gps(self, gps1, gps2):
        """
        Calculates the mean latitude and longitude of two given gps coordinates.
        This is used to centre the map produced by the compare_users function.
        """
        loc1 = self.geocode(gps1)
        gpsloc1 = [loc1.latitude, loc1.longitude]
        loc2 = self.geocode(gps2)
        gpsloc2 = [loc2.latitude, loc2.longitude]
        lat = np.mean([gpsloc1[0], gpsloc2[0]])
        longid = np.mean([gpsloc1[1], gpsloc2[1]])
        return [lat, longid]
