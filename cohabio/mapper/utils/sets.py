from collections import defaultdict

from cohabio.config import MODE_DISTANCE_FACTOR, MAX_BATCH_SIZE
from mapper.models import PlaceData, User
from mapper.utils.dt import next_week_day
from mapper.utils.geo import deg_from_km_sq
from mapper.googlemaps_client import gmaps_client


class EmptyIntersection(Exception):
    pass


class DynamicIntersection:
    min = 100  # Minimum locations to probe
    max = 200  # Maximum locations to probe
    curve = [(x / 30.0 - 0.45) ** 2 for x in range(10)]  # Growth curve for adjusting GPS border scale factor
    idx = 0  # Index values along curve
    scale = 1  # Initial scale factor
    iterations = 0  # Initial iteration number
    intersect = PlaceData.objects.none()

    @classmethod
    def _update(cls, *args):
        cls.intersect = args[0] & args[1]
        if cls.iterations == 0:
            cls.min = min(min(len(arg) for arg in args), cls.min)

    @classmethod
    def _decrease_scale(cls):
        cls.scale -= cls.curve[cls.idx]
        if cls.idx < 7:
            cls.idx += 1

    @classmethod
    def _increase_scale(cls):
        cls.scale += cls.curve[-1]

    @classmethod
    def adjusted_intersect(cls, user1, user2):
        """
        Reduces the user set boundaries until number of locations in intersect is < 200. This is to ensure there aren't
        too many requests made to Google Maps Distance Matrix API.
        """
        # TODO Convert print statements to logger messages
        while True:
            points1 = user1.get_nodes_within_boundary(cls.scale)
            points2 = user2.get_nodes_within_boundary(cls.scale)
            cls._update(points1, points2)
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            print('Locations in intersect: {}'.format(len(cls.intersect)))
            if cls.min <= len(cls.intersect) <= cls.max:
                print('Intersect locations between {} and {}. Ending'.format(cls.min, cls.max))
                break
            elif len(cls.intersect) < cls.min:
                print('Intersect locations below {}. Gradually increasing boundaries'.format(cls.min))
                cls._increase_scale()
            else:
                print('Intersect locations above {}. Reducing boundaries'.format(cls.max))
                cls._decrease_scale()
            if cls.iterations > 100:
                print('Ran through 100 iterations. Ending')
                break
            cls.iterations += 1
        return cls.intersect


class UserSet:
    def __init__(self, workplace, modes, max_time, geolocator, name="user"):
        self.workplace = workplace
        self.modes = modes
        self.max_time = float(max_time)
        origin = geolocator.coords_from_place_name(workplace)
        self.latitude = origin.latitude
        self.longitude = origin.longitude
        self.name = name
        self.boundary = []
        self.distance_factor = self._max_distance_factor()
        self.matches = defaultdict(list)
        self.model = User(workplace=workplace, transport=modes, max_commute=max_time, elements=0)
        self.model.save()

    def _max_distance_factor(self):
        """
        Find the transport type with biggest potential boundary.
        """
        return max([factor for mode, factor in MODE_DISTANCE_FACTOR.items() if mode in self.modes])

    def get_nodes_within_boundary(self, scale):
        """
        For a given scaling factor, adjusts a coordinate box around origin location and returns all PlaceData locations
        that fall within it.
        """
        scale_factor = scale * self.max_time / 60
        coord_adj = deg_from_km_sq(self.distance_factor * scale_factor)
        self.boundary = [[self.latitude - abs(coord_adj), self.longitude - 2*abs(coord_adj)],
                         [self.latitude + abs(coord_adj), self.longitude + 2*abs(coord_adj)]]
        return PlaceData.objects.filter(
            latitude__gte=self.boundary[0][0],
            latitude__lte=self.boundary[1][0],
            longitude__gte=self.boundary[0][1],
            longitude__lte=self.boundary[1][1]
        )

    @staticmethod
    def _iter_batches(iterable, n):
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]

    def filter_intersect_by_duration(self, intersect):
        arrival = next_week_day(self.latitude, self.longitude)
        try:
            for mode in self.modes:
                for batch in self._iter_batches(intersect, n=MAX_BATCH_SIZE):
                    result = gmaps_client.distance_matrix(
                        origins=((point.latitude, point.longitude) for point in batch),
                        destinations=(self.latitude, self.longitude),
                        mode=mode,
                        arrival_time=arrival
                    )
                    if result.get('status') == u'OK':
                        for idx, row in enumerate(result['rows']):
                            place = batch[idx]
                            element = row['elements'][0]
                            if element.get('status') == u'OK':
                                self.model.elements += 1
                                # Convert seconds to whole minutes.
                                duration = round(int(element['duration']['value']) / 60.0, 0)
                                if duration <= self.max_time:
                                    place.duration = duration
                                    self.matches[place].append((mode, duration))
                                    self.matches[place].sort(key=lambda x: x[1])
        finally:
            self.model.save()
        return intersect.filter(name__in=self.matches)
