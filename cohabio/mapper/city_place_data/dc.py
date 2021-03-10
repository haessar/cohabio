import http.client
import json

from tqdm import tqdm

from cohabio.config import WMATA_KEY

header = {
    'api_key': WMATA_KEY
}


def add_dc(model):
    conn = http.client.HTTPSConnection('api.wmata.com')
    conn.request("GET", "/Rail.svc/json/jStations", "{body}", header)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    stations = json.loads(data)['Stations']

    # Delete GeoNames record for Washington DC
    try:
        model.objects.get(name='Washington', country_code='US', source='geonames').delete()
    except Exception:
        pass

    for station in tqdm(stations, total=len(stations), desc='Washington DC stations'):
        place, created = model.objects.get_or_create(
            name=station['Name'],
            latitude=station['Lat'],
            longitude=station['Lon'],
            country_code='US',
            source='dc'
        )
        place.save()


def del_dc(model):
    model.objects.filter(source="dc").delete()
