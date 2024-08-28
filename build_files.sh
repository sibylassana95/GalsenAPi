#!/bin/bash

echo "BUILD START"

# Créer un environnement virtuel nommé 'venv' si ce n'est pas déjà fait
python3.12 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate

# Mettre à jour pip et setuptools
pip install --upgrade pip setuptools

# Installer les dépendances
pip install PyMySQL
pip install -r requirements.txt
pip install django-cors-headers

# Collecter les fichiers statiques
python3.12 manage.py collectstatic --noinput

# Créer le répertoire 'public/static' s'il n'existe pas
mkdir -p public/static

# Copier les fichiers statiques collectés dans 'public/static'
cp -r staticfiles/* public/static/

echo "BUILD END"
