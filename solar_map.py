import requests, json, time
from groundwater_database import get_coordinates
import pandas as pd


lat = list(lat)
lon = list(lon)

### API connection ###
token = 'f279e323e6b74c0d87bf5243f293fdc3f982f77b'
api_base = 'https://www.renewables.ninja/api/'
s = requests.session()
# Send token header with each request
s.headers = {'Authorization': 'Token ' + token}
url = api_base + 'data/pv'

output_data = []

for i, ii in zip(lat, lon):
    args = {
        'lat': i,
        'lon': ii,
        'date_from': '2023-01-01',
        'date_to': '2023-12-31',
        'capacity': 1.0,
        'system_loss': 0.1,
        'tracking': 0,
        'tilt': 35,
        'azim': 180,
        'format': 'json'
    }

    r = s.get(url, params=args)

    # Check if the response was successful
    if r.status_code == 200:
        try:
            parsed_response = json.loads(r.text)
            data = pd.read_json(json.dumps(parsed_response['data']), orient='index')
            output_data.append(data)
        except json.JSONDecodeError:
            print("JSON decoding failed. Response text:", r.text)
    else:
        print(f"Request failed with status code {r.status_code}. Response text:", r.text)

    time.sleep(75)  # Sleep for 75 seconds