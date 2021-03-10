from cohabio.secrets import *

# Place data
GEONAMES_FILENAME = 'cities500.txt'

"""
Values represent approximate km^2 box around any origin; a reasonable expected distance of travel for each
transport mode, when max_commute is 60 minutes (scale_factor).
"""
MODE_DISTANCE_FACTOR = {
    'transit': 125,
    'driving': 45,
    'bicycling': 10,
    'walking': 3
}

MARKER_SORTING_STD_WEIGHT = 0.2

"""
Google Maps Distance Matrix API parameters
"""
# Daily quota limit
MAX_ENTRIES = 100000

# Per request limit
MAX_BATCH_SIZE = 25
