<a name="readme-top"></a>

<div align="center">
  <img src="capture/logo.png" alt="logo" width="250"  height="auto" />
</div>


**GalsenApi** GalsenApi est une API qui vous permet de manipuler facilement des données sur le Sénégal. Ce projet s'inspire du package  **[Galsenify](https://www.npmjs.com/package/galsenify)**

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
#### Récupérer les informations sur le pays :
```http
  GET /api/pays/
```

## Utilisation
Pour récupérer toutes les régions :
GET  https://galsenapi.pythonanywhere.com/api/regions/

Exemple de résultat :
```json
{
    [
    {
        "id": 1,
        "nom": "Dakar",
        "code": "DK",
        "population": 4042225,
        "superficie": 547,
        "departments": [
            "Dakar",
            "Pikine",
            "Guédiawaye",
            "Rufisque",
            "Keur Massar"
        ]
    },
    {
        "id": 2,
        "nom": "Diourbel",
        "code": "DB",
        "population": 1980821,
        "superficie": 4824,
        "departments": [
            "Diourbel",
            "Bambey",
            "Mbacké"
        ]
    }]}
```
Pour récupérer une seule région :
https://galsenapi.pythonanywhere.com/api/regions/1/

Exemple de résultat :
```json

    {
    "id": 1,
    "nom": "Dakar",
    "code": "DK",
    "population": 4042225,
    "superficie": 547,
    "departments": [
        "Dakar",
        "Pikine",
        "Guédiawaye",
        "Rufisque",
        "Keur Massar"
    ]
}

```
## Captures d'écran
### Voici quelques captures d'écran pour illustrer les résultats de l'API :
### Récuperations des infos sur le pays
![CAPTURE](capture/pays.png)

### Récuperations de tout les Départements
![CAPTURE](capture/alldepartement.png)
### Récuperations d'un seul departement
![CAPTURE](capture/singledepartement.png)
### Récuperations de tout les Régions
![CAPTURE](capture/allregion.png)
### Récuperations d'une seul région
![CAPTURE](capture/singleregion.png)



## 👤 Author 

[![LASSANA SIBY](https://avatars.githubusercontent.com/u/103085452?u=13ace4d88a52056741734e0f802ca7c0053e1e80&v=4&s=40)](https://github.com/sibylassana95)  
Created by **[Lassana SIBY](https://github.com/sibylassana95)**

## Vous pouvez m'aider en faisant un don
  [![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/https://www.buymeacoffee.com/sibyamara9M)
  [![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/sibylassana) 



## 🔗 Links
[![portfolio](https://img.shields.io/badge/my_portfolio-000?style=for-the-badge&logo=ko-fi&logoColor=white)](https://sibylassana.com/)
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
    url = 'https://galsenapi.pythonanywhere.com/api/regions/'
    params = {'search': query} if query else {}
    response = requests.get(url, params=params)
    data = response.json()
    regions = data
    context = {'regions': regions, 'query': query}
    return render(request, 'demo/regions.html', context)


def departments_view(request):
    query = request.GET.get('q')
    url = 'https://galsenapi.pythonanywhere.com/api/departements/'
    params = {'search': query} if query else {}
    response = requests.get(url, params=params)
    data = response.json()
    departments = data
    context = {'departments': departments, 'query': query}
    return render(request, 'demo/departements.html', context)
```
![CAPTURE](capture/departement.png)
![CAPTURE](capture/region.png)

## 📝 LLicense

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

[![Made-In-Senegal](https://github.com/GalsenDev221/made.in.senegal/blob/master/assets/badge.svg)](https://github.com/GalsenDev221/made.in.senegal)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
