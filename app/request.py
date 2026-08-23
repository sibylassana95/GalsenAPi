import requests

response = requests.get('https://galsenapi.lassanasiby.com/api/regions/', timeout=30)
regions = response.json()

for region in regions:
    print(region['nom'])
    print(region['code'])
    print(region['population'])
    print(region['superficie'])
    print(region['departments'])
    print('-----------------------------------------------------')
