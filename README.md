<a name="readme-top"></a>
<div align="center">
  <img src="capture/logo.png" alt="logo" width="140" height="auto" />
  <h1>GalsenApi</h1>
  <p>
    Une API moderne pour accéder facilement aux données du Sénégal 🇸🇳
  </p>

  <p>
    <a href="./Licence.md">
      <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="mit" />
    </a>
    <a href="https://github.com/GalsenDev221/made.in.senegal">
      <img src="https://github.com/GalsenDev221/made.in.senegal/blob/master/assets/badge.svg" alt="made in senegal" />
    </a>
    <img src="https://img.shields.io/badge/version-2.0.0-blue" alt="version" />
  </p>

  <h4>
    <a href="https://galsenapi.vercel.app/">Démo</a>
    <span> · </span>
    <a href="https://galsenapi.vercel.app/docs/">Documentation</a>
    <span> · </span>
    <a href="EN.md">English version</a>
  </h4>
</div>

<br />

## 📋 Table des matières

- [Aperçu](#-aperçu)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Fonctionnalités](#-fonctionnalités)
- [Technologies](#-technologies)
- [Auteur](#-auteur)
- [Remerciements](#-remerciements)

## 🚀 Aperçu

**GalsenApi** est une API REST qui vous permet d'accéder facilement aux données du Sénégal. Ce projet s'inspire du package [Galsenify](https://www.npmjs.com/package/galsenify) et fournit des informations détaillées sur :

- Les régions du Sénégal
- Les départements
- Les arrondissements
- Les communes
- Les villages
- Les Universités et Ecole de formations
- Les données démographiques
- Et plus encore...

## ⚙️ Installation

1. Créez un environnement virtuel :

```bash
python -m venv .venv
```

2. Activez l'environnement virtuel :

```bash
source .venv/bin/activate
```

3. Installez les dépendances :

```bash
pip install requirements.txt
```

4. Effectuez les migrations :

```bash
python manage.py makemigrations
python manage.py migrate
```

5. Créez un super utilisateur :

```bash
python manage.py createsuperuser
```

6. Créez un fichier `.env` dans le projet Django pour stocker la clé secrète.

## 🎯 Utilisation

### Points d'accès de l'API

#### Récupérer toutes les régions

```http
GET /api/regions/
```

#### Récupérer une seule région

```http
GET /api/regions/1/
```

#### Récupérer tous les départements

```http
GET /api/departements
```

#### Récupérer un seul département

```http
GET /api/departements/1/
```

#### Récupérer tous les arrondissements

```http
GET /api/arrondissements/
```

#### Récupérer un seul arrondissement

```http
GET /api/arrondissements/1/
```

#### Récupérer toutes les communes

```http
GET /api/communes/
```

#### Récupérer une seule commune

```http
GET /api/communes/1/
```

#### Récupérer tous les villages

```http
GET api/villages
```

#### Récupérer un seul village

```http
GET /api/villages/1
```

#### Récupérer tous les Universités et Ecole de formations

```http
GET /api/universites/
```

#### Récupérer une universite ou ecole de formation

```http
GET /api/universites/1
```

#### Récupérer les informations sur le pays

```http
GET /api/pays/
```

## 💫 Fonctionnalités

- ✨ Interface utilisateur moderne et responsive
- 📱 Compatible mobile
- 🔍 Recherche avancée
- 📊 Données détaillées et à jour
- 🔒 Sécurisé et fiable

## 🛠 Technologies

- ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
- ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
- ![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
- ![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)

## 👤 Auteur

**Lassana SIBY**

[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sibylassana95)
[![LinkedIn](https://img.shields.io/badge/linkedin-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sibylassana)
[![Twitter](https://img.shields.io/badge/Twitter-%231DA1F2.svg?style=for-the-badge&logo=Twitter&logoColor=white)](https://twitter.com/sibyog13)

## 💝 Remerciements

### Merci à [Daouda BA](https://github.com/daoodaba975) pour les donées.
[![Daouda BA](https://avatars.githubusercontent.com/daoodaba975?s=64)](https://github.com/daoodaba975)

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
![CAPTURE](capture/home.png)

![CAPTURE](capture/galsenApi.png)

![CAPTURE](capture/galsenapi-vercel-app-region.png)

## 📝 License

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](./Licence.md)

[![Made-In-Senegal](https://github.com/GalsenDev221/made.in.senegal/blob/master/assets/badge.svg)](https://github.com/GalsenDev221/made.in.senegal)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<div align="center">
  <a href="https://www.buymeacoffee.com/sibyamara9M">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me A Coffee" />
  </a>
  <a href="https://paypal.me/sibylassana">
    <img src="https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal" />
  </a>
</div>