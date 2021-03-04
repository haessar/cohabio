"""
Functions that take two independent matrices of location coordinates, and return only the intersect locations that
satisfy commute time criteria.
"""
from collections import defaultdict
from operator import itemgetter

import numpy as np

from mapper.functions.google_API import gmaps_client, MAX_ENTRIES
from mapper.functions.datetime_tools import next_week_day, request_counter
from mapper.functions.geocoding_tools import deg_from_km_sq
from mapper.functions.prepare_markers import htmler
from mapper.models import PlaceData

"""
Values represent approximate km^2 box around any origin; a reasonable expected distance of travel for each
transport mode, when max_commute is 60 minutes (scale_factor).
"""
modes = {
    'transit': 125,
    'driving': 45,
    'bicycling': 10,
    'walking': 3
}

# TODO Convert print statements to logger messages in these functions


class UserFilterEmpty(Exception):
    pass


class UserMatrix(object):
    def __init__(self, origin, transport, max_commute):
        self.latitude = origin.latitude
        self.longitude = origin.longitude
        self.transport = self._reduce_transport_options(transport)
        self.max_commute = max_commute
        self.bounds = []

    @staticmethod
    def _reduce_transport_options(transport):
        """
        Find the transport type with biggest potential boundary.
        """
        for key, _ in sorted(modes.items(), key=lambda x: (x[1], x[0]), reverse=True):
            if key in transport:
                return key

    def get_user_matrix(self, scale):
        """
        For a given scaling factor, adjusts a coordinate box around origin location and returns all PlaceData locations
        that fall within it.
        """
        scale_factor = scale * float(self.max_commute) / 60
        coord_adj = deg_from_km_sq(modes[self.transport] * scale_factor)
        self.bounds = [[self.latitude - abs(coord_adj), self.longitude - 2*abs(coord_adj)],
                       [self.latitude + abs(coord_adj), self.longitude + 2*abs(coord_adj)]]
        return PlaceData.objects.filter(
            latitude__gte=self.bounds[0][0],
            latitude__lte=self.bounds[1][0],
            longitude__gte=self.bounds[0][1],
            longitude__lte=self.bounds[1][1]
        )


class LocationIntersection(object):
    min = 100  # Minimum locations to probe
    max = 200  # Maximum locations to probe
    curve = [(x / 30.0 - 0.45) ** 2 for x in range(10)]  # Growth curve for adjusting GPS border scale factor
    idx = 0  # Index values along curve
    scale = 1  # Initial scale factor
    iterations = 0  # Initial iteration number

    def update(self, *args):
        self.intersect = args[0] & args[1]
        if self.iterations == 0:
            self.min = min(min(len(arg) for arg in args), self.min)

    def decrease_scale(self):
        self.scale -= self.curve[self.idx]
        if self.idx < 7:
            self.idx += 1

    def increase_scale(self):
        self.scale += self.curve[-1]


def adjust_intersect(locations, modes, times):
    """
    Reduces the user matrix boundaries until number of locations in intersect is < 200. This is to ensure there aren't
    too many requests made to Google Maps Distance Matrix API.
    """
    user1 = UserMatrix(origin=locations[0], transport=modes[0], max_commute=times[0])
    user2 = UserMatrix(origin=locations[1], transport=modes[1], max_commute=times[1])
    li = LocationIntersection()
    while True:
        probes1 = user1.get_user_matrix(li.scale)
        probes2 = user2.get_user_matrix(li.scale)
        li.update(probes1, probes2)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('Locations in intersect: {}'.format(str(len(li.intersect))))
        if li.min <= len(li.intersect) <= li.max:
            print('Intersect locations between {} and {}. Ending'.format(str(li.min), str(li.max)))
            break
        elif len(li.intersect) < li.min:
            print('Intersect locations below {}. Gradually increasing boundaries'.format(str(li.min)))
            li.increase_scale()
        else:
            print('Intersect locations above {}. Reducing boundaries'.format(str(li.max)))
            li.decrease_scale()
        if li.iterations > 100:
            print('Ran through 100 iterations. Ending')
            break
        li.iterations += 1
    return li.intersect


def batches(iterable, n):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def which_duration(output, user, origin, destinations, transport, max_commute):
    """
    Takes origin string and location list of any size and returns the time in minutes between them for given method
    of transport.
    """
    arrival = next_week_day(origin)
    count = 0
    # Maximum of 25 destinations in a given distance_matrix API call (without premium)
    for batch in batches(destinations, n=25):
        result = gmaps_client.distance_matrix(
            origins=((dest.latitude, dest.longitude) for dest in batch),
            destinations=(origin.latitude, origin.longitude),
            mode=transport,
            arrival_time=arrival
        )
        if result.get('status') == u'OK':
            result = zip(result.get('rows'), batch)
            for (row, place) in result:
                if row['elements'][0].get('status') == u'OK':
                    # Convert seconds to whole minutes.
                    duration = round(int(row['elements'][0].get('duration').get('value')) / 60.0, 0)
                    if duration <= int(max_commute):
                        if not output[place]:
                            output[place] = defaultdict(list)
                        output[place][user].append((transport, duration))
                        # Sort by duration
                        output[place][user].sort(key=itemgetter(1))
                        count += 1
    if count == 0:
        raise UserFilterEmpty('{} locations empty after filtering for max commute time for {}'.format(user, transport))
    print('{} locations after filtering for max commute time for {}: {}'.format(user, transport, count))


def probe_gps_intersect(locations, modes, times, geolocator):
    """
    Find common pairs in both sets of probes, and remove duplicates. Then filter for max_commute times
    """
    origins = geolocator.return_gps_from_place_names(locations)
    intersect = adjust_intersect(origins, modes, times)
    quota_today = request_counter()
    entry_count = 0
    if len(intersect) == 0:
        print('Empty intersection before filter')
        return 'empty', entry_count
    output = defaultdict(dict)
    for i, prefs in enumerate(zip(origins, modes, times)):
        user = 'user' + str(i + 1)
        for mode in prefs[1]:
            entry_count += len(intersect)
            if quota_today + entry_count >= MAX_ENTRIES:
                print('Maximum daily quota reached during {} distance_matrix API call'.format(user))
                return 'maxed', entry_count
            try:
                which_duration(output, user, prefs[0], intersect, mode, prefs[2])
            except UserFilterEmpty:
                return 'empty', entry_count
    for place, values in output.copy().items():
        if len(values) == len(origins):
            # User list was already sorted by shortest duration, so we take tuple at 0th index.
            # Duration is at 1st index of this.
            durations = [values.get(user)[0][1] for user in values]
            values['mean'] = np.mean(durations)
            values['stds'] = np.std(durations)
            values['html'] = htmler(place, values)
        else:
            del output[place]
    if not output:
        print('Intersection of locations empty after filtering for max commute times')
        return 'empty', entry_count
    return output, entry_count
