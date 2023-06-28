FROM python:3.9-slim

WORKDIR /app

RUN apt-get update -qq && apt-get -y --no-install-recommends install \
    build-essential \
    curl \
    software-properties-common &&\
    rm -rf /var/lib/apt/lists/*

COPY app.py ./app.py
COPY /src ./src
COPY /subpages ./subpages
COPY /data ./data
COPY /images    ./images 
COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
