from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderQuotaExceeded, GeocoderTimedOut
from math import cos
import numpy as np
import time

def gps_from_km_sq(km, loc_lat):
    """
    Determines the latitude and longitude coordinates that approximate the lengths of a given km square value.
    """
    lat = km * 0.008983 / 2
    lng = km * (360 / (cos(loc_lat) * 40075)) / 2
    return lat, lng

class GeoLocator(GoogleV3):
    api_key = 'AIzaSyDwNieaCFdsNt5Xp_Kuq-YK0bG2uUX5cI8'
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
        Calculates the mean latitude and longitude of two given gps coordinates. This is used to centre the map produced by
        the compare_users function.
        """
        loc1 = self.geocode(gps1)
        gpsloc1 = [loc1.latitude, loc1.longitude]
        loc2 = self.geocode(gps2)
        gpsloc2 = [loc2.latitude, loc2.longitude]
        lat = np.mean([gpsloc1[0], gpsloc2[0]])
        longid = np.mean([gpsloc1[1], gpsloc2[1]])
        return [lat, longid]
