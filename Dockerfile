FROM python:3.9

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmysqlclient-dev \
    build-essential \
    pkg-config \
    python3-dev

# Set up the environment
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
