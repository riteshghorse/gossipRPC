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

### cmds for runnning the docker:
1. a. docker build -t gossip .  -> builds docker image
   b. docker network create --driver bridge gossip-network -> creates network

2. docker run -it --name monitor-node --network gossip-network gossip -> run the docker image
   Inside the terminal app_user@bd390faf66db:~$ python Monitoring_Node.py --config ./config/monitor.json -> this is like a new terminal use it as monitor-node 

3. Provider Node
    docker run -it --name provider-node --network gossip-network gossip -> run the docker image
   Inside the terminal app_user@bd390faf66db:~$ python Provider_Node.py --config ./config/provider.json -> this is like a new terminal use it as provider-node

4. new terminal for node 1
   docker run -it --name node1 --network gossip-network gossip
   Inside the terminal app_user@bd390faf66db: python gossip_server.py --config ./config/config1.json

5. new terminal for node 2
    docker run -it --name node2 --network gossip-network gossip
    Inside the terminal app_user@bd390faf66db: python gossip_server.py --config ./config/config1.json

6. Normal node
    docker run -it --network gossip-network gossip
    Inside the terminal app_user@bd390faf66db: python gossip_server.py

7. docker rm $(docker ps --filter name=node* -aq) --> kill the docker dameon running earlier