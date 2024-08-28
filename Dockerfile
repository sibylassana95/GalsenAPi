# Utiliser une image de base avec Python
FROM python:3.9

# Installer les dépendances système nécessaires
RUN apt-get update && \
    apt-get install -y \
    libmysqlclient-dev \
    build-essential \
    pkg-config \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier des dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copier le reste de l'application
COPY . .

# Exécuter les migrations et collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Commande par défaut pour démarrer l'application
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
