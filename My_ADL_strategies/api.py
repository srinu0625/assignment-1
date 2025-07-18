import requests

# Public test API – no keys needed
url = "https://www.bitget.site/price/pi-network"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("Title:", data['title'])
    print("Body:", data['body'])
else:
    print("Failed to fetch data. Status code:", response.status_code)
