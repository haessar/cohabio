"""
Functions that take two independent matrices of location coordinates, and return only the intersect locations that
satisfy commute time criteria.
"""
from collections import defaultdict

import numpy as np

from cohabio.config import MARKER_SORTING_STD_WEIGHT
from mapper.models import SearchResults
from mapper.utils.pins import htmler, sorter
from mapper.utils.sets import DynamicIntersection, EmptyIntersection


def compare_users(user1, user2):
    """
    Find common pairs in both sets of probes, and remove duplicates. Then filter for max_commute times
    """
    output = defaultdict(dict)
    try:
        intersect = DynamicIntersection.adjusted_intersect(user1, user2)
        if len(intersect) == 0:
            raise EmptyIntersection('Empty intersection before filter')
        intersect = user1.filter_intersect_by_duration(intersect)
        intersect = user2.filter_intersect_by_duration(intersect)

        for place in intersect:
            # User list was already sorted by shortest duration, so we take tuple at 0th index.
            # Duration is at 1st index of this.
            durations = [user.matches.get(place)[0][1] for user in [user1, user2]]
            mean = np.mean(durations)
            std = np.std(durations)
            output[place]['mean'] = mean
            output[place]['std'] = std
            output[place]['html'] = htmler(place, mean, std, user1, user2)
        if not output:
            raise EmptyIntersection('Intersection of locations empty after filtering for max commute times')
    finally:
        search_results = SearchResults(
            you=user1.model,
            them=user2.model,
            results=len(output)
        )
        search_results.save()
    return sorter(output, MARKER_SORTING_STD_WEIGHT)
