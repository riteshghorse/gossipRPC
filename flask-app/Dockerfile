# Author: Tanvi P
# Docker file for setting up the flask server in a isolated(virtual env) and containerized environment

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt

RUN [ "pip", "install", "--upgrade", "pip" ]

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]