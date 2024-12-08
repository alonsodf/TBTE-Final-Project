import sys, json, requests, time
from urllib.request import urlopen
from groundwater_database import get_coordinates

def make_url():
    nrel_api_key = 'nrE78X1ApOcYUea52exv7CuxpvpAXkKHdebJZwal'
    url = 'https://developer.nrel.gov/api/nsrdb/v2/solar/himawari7-download.json?api_key=%s' % (nrel_api_key)
    return url

def check_url(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return 'bad'
        return 'good'
    except requests.exceptions.RequestException as e:
        print(f"Error checking URL: {e}")
        return 'bad'

def get_payload(lat, lon):
    payload = 'wkt=POINT(%f %f)&attributes=gni,dni,dhi&names=2015&utc=false&interval=60&email=alonso.fernandez@utexas.edu' % (lat, lon)
    return payload

def get_response(url, payload):
    headers = {
    'content-type': "application/x-www-form-urlencoded",
    'cache-control': "no-cache"
    }
    try:
        response = requests.request("POST", url, data=payload, headers=headers)
        print(response.text)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error making POST request: {e}")
        return None