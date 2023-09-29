import requests

url = "https://api.hostfully.com/v2/properties?agencyUid=d3dcb567-03dc-4c17-8918-e119b0bd579d&limit=20&offset=0"

headers = {
    "accept": "application/json",
    "X-HOSTFULLY-APIKEY": "tAryEQrD4HRUqAxF"
}

response = requests.get(url, headers=headers)

print(response.text)