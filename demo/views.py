import requests
from django.shortcuts import render


def pays_view(request):
    response = requests.get('https://galsenapi.pythonanywhere.com/api/pays/')
    data = response.json()
    data_pays = data
    context = {'data': data_pays}

    return render(request, 'demo/pays.html', context)


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
