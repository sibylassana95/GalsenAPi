<a name="readme-top"></a>

<div align="center">
  <img src="capture/logo.png" alt="logo" width="250"  height="auto" />
</div>


**GalsenApi**  est une API qui vous permet de manipuler facilement des données sur le Sénégal. Ce projet s'inspire du package  **[Galsenify](https://www.npmjs.com/package/galsenify)**

***Read in [English](EN.md)***
## Installation 💻 

- Créez un environnement virtuel :

```bash
  python -m venv .venv
```
- Activez l'environnement virtuel :

```bash
  source .venv/bin/activate
```  
- Installez les dépendances :

```bash
  pip install requirements.txt
```
- Effectuez les migrations :

```bash
  python manage.py makemigrations
  python manage.py migrate
```    
- Créez un super utilisateur :

```bash
  python manage.py createsuperuser
  
```
- Lancez le serveur :

```bash
  python manage.py runserver
  
```
Créez un fichier .env dans le projet Django pour stocker la clé secrète.

## API Reference
#### Voici les différentes méthodes d'API disponibles :
#### Récupérer toutes les régions :
```http
  GET /api/regions/
```
#### Récupérer une seule région :
```http
  GET /api/regions/1/
```
#### Récupérer tous les départements :
```http
  GET /api/departements
```
#### Récupérer un seul département :
```http
  GET /api/departements/1/
```
#### Récupérer tous les villages :
```http
  GET api/villages
```
#### Récupérer un seul département :
```http
  GET /api/villages/1
```
#### Récupérer les informations sur le pays :
```http
  GET /api/pays/
```

## Pour plus d'information consulter la documentation 
# **[Documentation 🚀](https://galsenapi.vercel.app/docs)**


## 👤 Author 

[![LASSANA SIBY](https://avatars.githubusercontent.com/u/103085452?u=13ace4d88a52056741734e0f802ca7c0053e1e80&v=4&s=40)](https://github.com/sibylassana95)  
Created by **[Lassana SIBY](https://github.com/sibylassana95)**

  [![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/sibyamara9M)
  [![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/sibylassana) 



## 🔗 Links
[![portfolio](https://img.shields.io/badge/my_portfolio-000?style=for-the-badge&logo=ko-fi&logoColor=white)](https://sibylassana.vercel.app/)
[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sibylassana/)
[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/sibyog13)

### Merci à [Daouda BA](https://github.com/daoodaba975) pour les donées.
[![Daouda BA](https://avatars.githubusercontent.com/daoodaba975?s=64)](https://github.com/daoodaba975)

## **[Demo 🚀](https://galsenapi.pythonanywhere.com/)**

### Exemple d'utilisation de l'api 
Views region et departement
```python
def regions_view(request):
    query = request.GET.get('q')
    url = 'https://galsenapi.vercel.app/api/regions/'
    params = {'search': query} if query else {}
    response = requests.get(url, params=params)
    data = response.json()
    regions = data
    context = {'regions': regions, 'query': query}
    return render(request, 'demo/regions.html', context)


def departments_view(request):
    query = request.GET.get('q')
    url = 'https://galsenapi.vercel.app/api/departements/'
    params = {'search': query} if query else {}
    response = requests.get(url, params=params)
    data = response.json()
    departments = data
    context = {'departments': departments, 'query': query}
    return render(request, 'demo/departements.html', context)

def villages_view(request):
    query = request.GET.get('q')
    url = 'https://galsenapi.vercel.app/api/villages/'
    params = {'search': query} if query else {}
    response = requests.get(url, params=params)
    data = response.json()
    villages = data
    context = {'villages': villages, 'query': query}
    return render(request, 'demo/village.html', context)    
```
![CAPTURE](capture/departement.png)
![CAPTURE](capture/region.png)
![CAPTURE](capture/villages.png)

## 📝 License

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](./Licence.md)

[![Made-In-Senegal](https://github.com/GalsenDev221/made.in.senegal/blob/master/assets/badge.svg)](https://github.com/GalsenDev221/made.in.senegal)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
