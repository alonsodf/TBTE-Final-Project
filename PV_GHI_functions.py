import sys, json, time, requests
from urllib.request import urlopen
import pandas as pd
## Using NREL API to get GHI data for all well locations
## Want to write a script that optimizes the TDS level, well depth, and GHI
## And to only keepy the 50 best to then go get capacity factors for those locations from Ninja Renewables API

coordinates = pd.read_excel(r"C:\Users\Alonso\OneDrive - The University of Texas at Austin\UT\Research\03 Data\well_coordinates.xlsx")

def make_url():
    nrel_api_key = ''
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
    payload = r'wkt=POINT({lon} {lat})&attributes=gni,dni,dhi&names=2015&utc=true&interval=60&email=alonso.fernandez@utexas.edu'
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
    
def main():
    # Get the coordinates dataframe from groundwater_database
    
    # Make the URL
    url = make_url()
    print(f"URL: {url}")

    # Check if the URL is good
    if check_url(url) == 'bad':
        print("URL is not accessible.")
        return
    
    results = []
    for index, row in coordinates.iterrows():
        lat = row['latitude']
        lon = row['longitude']

        payload = get_payload(lat, lon)
        print(f"Payload: {payload}")

        response = get_response(url, payload)

        if response:
            results.append(response)
        else:
            print("No response received.")

if __name__ == "__main__":
    main()