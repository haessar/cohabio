import http.client
import json

import pandas as pd

from cohabio.config import WMATA_KEY

header = {
    'api_key': WMATA_KEY
}

cols = ['name', 'latitude', 'longitude']


def add_washington_dc(model):
    conn = http.client.HTTPSConnection('api.wmata.com')
    conn.request("GET", "/Rail.svc/json/jStations", "{body}", header)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    stations = json.loads(data)['Stations']
    stations = pd.DataFrame(stations).rename(columns={'Name': 'name', 'Lat': 'latitude', 'Lon': 'longitude'})

    # Delete GeoNames record for Washington DC
    try:
        model.objects.get(name='Washington', country_code='US', source='geonames').delete()
    except Exception:
        pass

    yield stations[cols].to_dict('records')
