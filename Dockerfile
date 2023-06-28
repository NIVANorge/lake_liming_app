FROM python:3.10.6

WORKDIR /app

RUN apt-get update -qq &&\
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

COPY app.py ./app.py
COPY /src ./src
COPY /subpages ./subpages
COPY /data ./data
COPY /images ./images 


EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
