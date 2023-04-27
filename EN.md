<a name="readme-top"></a>

<div align="center">
  <img src="capture/logo.png" alt="logo" width="250"  height="auto" />
</div>


**GalsenApi** is an API that allows you to easily manipulate data on Senegal. A project inspired by the package. **[Galsenify](https://www.npmjs.com/package/galsenify)**


## Installation 💻 

- Create a virtual environment:

```bash
  python -m venv .venv
```
- Activate the virtual environment:

```bash
  source .venv/bin/activate
```  
- Install the dependencies:

```bash
  pip install requirements.txt
```
- Run the migrations:

```bash
  python manage.py makemigrations
  python manage.py migrate
```    
- Create a super user:

```bash
  python manage.py createsuperuser
  
```
- Create a .env file in the Django project to store the secret key.

## API Reference

#### Get all regions 
```http
  GET /api/regions/
```
#### Get a single region
```http
  GET /api/regions/1/
```
#### Get all departments
```http
  GET /api/departements
```
#### Get a single department
```http
  GET /api/departements/1/
```
#### Get all villages :
```http
  GET api/villages
```
#### Get a single village :
```http
  GET /api/villages/1
```
#### Get country information
```http
  GET /api/pays/
```

## Usage
To get all regions, use a GET request:
https://galsenapi.pythonanywhere.com/api/regions/

Example Result
```json
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
    }]
```
To get a single region, use a GET request:
https://galsenapi.pythonanywhere.com/api/regions/1/

Example Result
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
## Capture
### Retrieval of information about the country
![CAPTURE](capture/pays.png)

### Retrieval of all Departments
![CAPTURE](capture/alldepartement.png)
### Retrieval of a single department
![CAPTURE](capture/singledepartement.png)
### Retrieval of all Regions
![CAPTURE](capture/allregion.png)
### Retrieval off a single Region
![CAPTURE](capture/singleregion.png)



## 👤 Author 

[![LASSANA SIBY](https://avatars.githubusercontent.com/u/103085452?u=13ace4d88a52056741734e0f802ca7c0053e1e80&v=4&s=40)](https://github.com/sibylassana95)  
Created by **[Lassana SIBY](https://github.com/sibylassana95)**

  [![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/https://www.buymeacoffee.com/sibyamara9M)
  [![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/sibylassana) 


## 🔗 Links
[![portfolio](https://img.shields.io/badge/my_portfolio-000?style=for-the-badge&logo=ko-fi&logoColor=white)](https://sibylassana.com/)
[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sibylassana/)
[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/sibyog13)

### Thank you to [Daouda BA](https://github.com/daoodaba975) for the data..
[![Daouda BA](https://avatars.githubusercontent.com/daoodaba975?s=64)](https://github.com/daoodaba975)

## **[Demo 🚀](https://galsenapi.pythonanywhere.com/)**

### Example of using the API
Views for regions and departments.
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

def villages_view(request):
    query = request.GET.get('q')
    url = 'https://galsenapi.pythonanywhere.com/api/villages/'
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
