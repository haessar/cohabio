"""
Functions for ordering and preparing the markers for HTML
"""

from collections import OrderedDict


"""
Map transport mode to Font Awesome icon.
"""
HTML_ICON_MAP = {
    'walking': 'fa-male',
    'bicycling': 'fa-bicycle',
    'driving': 'fa-car',
    'transit': 'fa-train',
}


def html_check(transports):
    """For transport option memory"""
    trans_vec = ['walking', 'bicycling', 'driving', 'transit']
    which_checked = [index for index, item in enumerate(trans_vec) if item in transports]
    out_checked = ['', '', '', '']
    out_active = ['', '', '', '']
    html_checked = ['checked', 'checked', 'checked', 'checked']
    html_active = ['active', 'active', 'active', 'active']
    for (index, replacement) in zip(which_checked, html_active):
        out_active[index] = replacement
    for (index, replacement) in zip(which_checked, html_checked):
        out_checked[index] = replacement
    return [out_active, out_checked]

def htmler(place, values):
    user_template = '<p>Travel time for {user}: <i class="fa {icon}"></i> {duration} mins{duplicate}</p>'
    user_html = ''
    for user in args:
        match = user.matches.get(place)
        if len(match) == 1:
            duplicate = ''
        else:
            duplicate = ' (<i class="fa {icon}"></i> {duration} mins)'.format(
                icon=HTML_ICON_MAP.get(match[1][0]),
                duration=int(match[1][1])
            )
        user_html += user_template.format(
            user=user.name,
            icon=HTML_ICON_MAP.get(match[0][0]),
            duration=int(match[0][1]),
            duplicate=duplicate
        )
    return '<h3>{place}</h3>{user_html}<h4>Mean travel time: {mean} mins</h4><h4>Standard deviation: {std} mins</h4>'.format(
        place=place,
        user_html=user_html,
        mean=values['mean'],
        std=values['stds']
    )


def sorter(data, std_weight):
    return OrderedDict(sorted(data.items(), key=lambda x: x[1]['mean'] + std_weight * x[1]['stds']))
