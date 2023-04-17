
# GalsenApi

**GalsenApi** est un api qui vous permet de manipuler facilement des données sur le Sénégal.Un projet inspirer du package **[Galsenify](https://www.npmjs.com/package/galsenify)**


## Installation

Crée l'environement virtuel

```bash
  python -m venv .venv
```
Activer l'environement virtuel

```bash
  source .venv/bin/activate
```  
Installer les dépendances

```bash
  pip install requirements.txt
```
Faire les migrations

```bash
  python manage.py makemigrations
  python manage.py migrate
```    
Créer un super utulisateur 

```bash
  python manage.py createsuperuser
  
```
Créer un fichier .env dans le projet django pour stocker le secret key

## API Reference

#### Recuperer tous les Régions 
```http
  GET /api/regions/
```
#### Recuperer une seul région
```http
  GET /api/regions/1/
```
#### Recuperer  tous les départements
```http
  GET /api/departements
```
#### Recuperer un seul département
```http
  GET /api/departements/1/
```
#### Recuperer les infos du pays
```http
  GET /api/pays/
```

## Usage
Pour recuperer tous les Régions GET
https://galsenapi.pythonanywhere.com/api/regions/

exemple de resultat
```javascript
{
    "count": 14,
    "next": "https://galsenapi.pythonanywhere.com/api/regions/?page=2",
    "previous": null,
    "results": [
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
        },
```
Pour recuperer une seul regions GET
https://galsenapi.pythonanywhere.com/api/regions/1/

exemple de resultat
```javascript
{
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
## Capture
Récuperations des infos sur le pays
![CAPTURE](capture/pays.png)

Récuperations de tout les Départements
![CAPTURE](capture/alldepartement.png)
Récuperations d'un seul departement
![CAPTURE](capture/singledepartement.png)
Récuperations de tout les Régions
![CAPTURE](capture/allregion.png)
Récuperations d'une seul région
![CAPTURE](capture/singleregion.png)



## Author 🌟

[![LASSANA SIBY](https://avatars.githubusercontent.com/u/103085452?u=13ace4d88a52056741734e0f802ca7c0053e1e80&v=4&s=40)](https://github.com/sibylassana95)  
Created by **[Lassana SIBY](https://github.com/daoodaba975)**



## 🔗 Links
[![portfolio](https://img.shields.io/badge/my_portfolio-000?style=for-the-badge&logo=ko-fi&logoColor=white)](https://sibylassana.com/)
[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sibylassana/)
[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/sibyog13)

Un merci spécial à [Daouda BA)](https://github.com/daoodaba975) pour les donées.

## Demo

### Exemple d'utilisation de l'api 
![CAPTURE](capture/departement.png)
![CAPTURE](capture/region.png)
https://galsenapi.pythonanywhere.com/
## License

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

[![Made-In-Senegal](https://github.com/GalsenDev221/made.in.senegal/blob/master/assets/badge.svg)](https://github.com/GalsenDev221/made.in.senegal)


