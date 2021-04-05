FROM python:3.8

RUN [ "mkdir", "-p", "/usr/src/app" ]

WORKDIR /usr/src/app

#COPY requirements.txt requirements.txt

#RUN [ "pip", "install", "--upgrade", "pip" ]

#RUN [ "pip", "install", "-r", "requirements.txt" ]

COPY . .

#CMD ["python", "src/gossip_server.py"#]
