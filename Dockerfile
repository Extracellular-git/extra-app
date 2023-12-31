FROM python:3.11-slim

COPY . /app

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install -r requirements.txt

EXPOSE 9501

HEALTHCHECK CMD curl --fail http://localhost:9501/_stcore/health

ENTRYPOINT ["streamlit", "run", "Home.py"]
