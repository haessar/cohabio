import googlemaps

from cohabio.config import GOOGLE_KEY, GOOGLE_CLIENT_ID


gmaps_client = googlemaps.Client(
    key=GOOGLE_KEY,
    client_id=GOOGLE_CLIENT_ID
)
