echo "BUILD START"

# Créez un environnement virtuel s'il n'existe pas déjà
python3.9 -m venv venv

# Activez l'environnement virtuel
source venv/bin/activate
pip install --upgrade setuptools

# Installez toutes les dépendances dans l'environnement virtuel
pip install -r requirements.txt
python manage.py collectstatic --noinput
# Installez django-cors-headers si ce n'est pas déjà fait
pip install django-cors-headers



# Collectez les fichiers statiques
python manage.py collectstatic --noinput

echo "BUILD END"

