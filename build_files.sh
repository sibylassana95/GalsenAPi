echo "BUILD START"

# create a virtual environment named 'venv' if it doesn't already exist
python3.9 -m venv venv

# activate the virtual environment
source venv/bin/activate

# install build dependencies (no need for sudo in this script)
apt-get update
apt-get install -y pkg-config python3-dev default-libmysqlclient-dev build-essential

# install all dependencies in the venv
pip install --upgrade pip setuptools
pip install -r requirements.txt
pip install django-cors-headers

# collect static files using the Python interpreter from venv
rm -rf staticfiles_build/static/
python manage.py collectstatic --noinput

echo "BUILD END"
