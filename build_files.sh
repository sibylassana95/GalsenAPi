
echo "BUILD START"

# create a virtual environment named 'venv' if it doesn't already exist
python3.9 -m venv venv

# activate the virtual environment
source venv/bin/activate
pip install --upgrade setuptools
# install all deps in the venv
pip install -r requirements.txt
pip install django-cors-headers
# collect static files using the Python interpreter from venv
python3.9 manage.py collectstatic --noinput 

echo "BUILD END"

# [optional] Start the application here 
# python manage.py runserver