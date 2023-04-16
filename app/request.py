import requests

response = requests.get('https://galsenapi.pythonanywhere.com/api/regions/') # Remplacez l'URL par celle de votre serveur
regions = response.json()
print (regions)


