"""
Parameters for using Google's distance matrix API
"""

import googlemaps

'''Dave's API key'''
# gmaps = googlemaps.Client(key = 'AIzaSyCaFOvBe4pgrvksrj3XPMb7gnX2blXHMio')

'''Will's API key'''
gmaps = googlemaps.Client(
    key='AIzaSyD0igbjpP02XgmFnW390I5IFlyvxTLYgOs',
    client_id='610519970507-5jm3d5dl2plppmegvl0evsaotlpetqpg.apps.googleusercontent.com'
)

''' Daily quota limit '''
max_entries = 2500
