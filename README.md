## Steps for running Flask

#### 1. Installation

```
pip install flask
```

### 2.Set Flask Application Name

```
export FLASK_APP=app
```

### 3. Set Development Environment for Flask

```
export FLASK_ENV=development
```

### 4. Running Application

```
flask run
```

Note: This step assumes that Monitoring Node is already runnning.

## Steps for running Docker

### Spin up the containers

```
docker-compose up -d --build
```

### Entering into the container

```
sudo docker exec -it <container-name> /bin/bash
```

### Adding a new container into the network without docker-compose

- Make sure you create an image for the code beforehand

```
    docker build -t gossip <path-to-Dockerfile>
```

- Run the container 

```
    docker run -it --name <container-name-optional> --network gossiprpc_default gossip
 ```


