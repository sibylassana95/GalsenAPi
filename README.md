
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
Récuperations de tout les département
![CAPTURE](capture/alldepartement.png)



## Author 🌟

[![Daouda BA](https://avatars.githubusercontent.com/u/103085452?u=13ace4d88a52056741734e0f802ca7c0053e1e80&v=4&s=40)](https://github.com/sibylassana95)  
Created by **[Lassana SIBY](https://github.com/daoodaba975)**



## 🔗 Links
[![portfolio](https://img.shields.io/badge/my_portfolio-000?style=for-the-badge&logo=ko-fi&logoColor=white)](https://sibylassana.com/)
[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sibylassana/)
[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/sibyog13)


## Demo

Exemple d'utilisation de l'api 

https://galsenapi.pythonanywhere.com/
## License

[MIT](https://choosealicense.com/licenses/mit/)
[![Made-In-Senegal](https://github.com/GalsenDev221/made.in.senegal/blob/master/assets/badge.svg)](https://github.com/GalsenDev221/made.in.senegal)


