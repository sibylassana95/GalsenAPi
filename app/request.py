import requests

response = requests.get('https://galsenapi.vercel.app/api/regions/') # Remplacez l'URL par celle de votre serveur
regions = response.json()

for region in regions:
    print(region['nom'])
    print(region['code'])
    print(region['population'])
    print(region['superficie'])
    print(region['departments'])
    print('-----------------------------------------------------')

