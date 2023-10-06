FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone -b live https://github.com/extracellular-git/extra-app.git .

RUN pip3 install -r requirements.txt

EXPOSE 9501

HEALTHCHECK CMD curl --fail http://localhost:9501/_stcore/health

ENTRYPOINT ["streamlit", "run", "Home.py"]