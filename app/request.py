import requests

response = requests.get('https://galsenapi.pythonanywhere.com/api/regions/')
regions = response.json()
print (regions)


