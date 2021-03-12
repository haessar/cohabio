import http.client
import json

import pandas as pd

from cohabio.config import WMATA_KEY

header = {
    'api_key': WMATA_KEY
}

cols = ['name', 'latitude', 'longitude']


def add_washington_dc():
    conn = http.client.HTTPSConnection('api.wmata.com')
    conn.request("GET", "/Rail.svc/json/jStations", "{body}", header)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    stations = json.loads(data)['Stations']
    stations = pd.DataFrame(stations).rename(columns={'Name': 'name', 'Lat': 'latitude', 'Lon': 'longitude'})

    yield stations[cols].to_dict('records')
