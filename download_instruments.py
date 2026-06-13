import urllib.request
import json

instrument_url = (
    "https://margincalculator.angelbroking.com/"
    "OpenAPI_File/files/OpenAPIScripMaster.json"
)

response = urllib.request.urlopen(instrument_url)

instrument_list = json.loads(response.read())

with open("data/instruments.json", "w") as f:
    json.dump(instrument_list, f)

print(f"Saved {len(instrument_list)} instruments")