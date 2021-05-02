## Steps for running Flask

1. #### Installation

```
pip install flask
```

2. ### Set Flask Application Name

```
export FLASK_APP=app
```

3. ###  Set Development Environment for Flask

```
export FLASK_ENV=development
```

4. ###  Running Application

```
flask run
```

Note: This step assumes that Monitoring Node is already runnning.

## Steps for running Docker-Compose

1. ### Build image of the application
    ```
    docker build -t gossip <path-to-Dockerfile>
    ```
1. ### Spin up the containers
    * When doing it for the first time
    ```
    docker-compose up -d --build --scale node=<no of containers to spin apart from seed nodes>
    ```
    * For subsequent runs when the image is the same
    ```
    docker-compose up -d --scale node=<no of containers to spin apart from seed nodes>
    ```

2. ### Entering into the container

```
sudo docker exec -it <container-name> /bin/bash
```
Note:
3. ### Adding a new container into the network without docker-compose

* Make sure you create an image for the code beforehand

```
    docker build -t gossip <path-to-Dockerfile>
```

* Run the container

```
    docker run -it --name <container-name-optional> --network gossip_network gossip
```

## Running as standalone docker containers

1.
    * docker build -t gossip . -> builds docker image
    * docker network create --driver bridge gossip-network -> creates network

2.
    * docker run -it --name monitor-node --network gossip-network gossip -> run the docker image
    * Inside the terminal

    ```
    app_user@bd390faf66db:~$ python Monitoring_Node.py --config ./config/monitor.json 
    ```

    -> this is like a new terminal use it as monitor-node

3. Provider Node
   * docker run -it --name provider-node --network gossip-network gossip -> run the docker image
   Inside the terminal

   ```
   app_user@bd390faf66db:~$ python Provider_Node.py --config ./config/provider.json 
   ```

   -> this is like a new terminal use it as provider-node

4. New terminal for node 1
   * docker run -it --name node1 --network gossip-network gossip
   * Inside the terminal

   ```
   app_user@bd390faf66db: python gossip_server.py --config ./config/config1.json
   ```

5. New terminal for node 2
   * docker run -it --name node2 --network gossip-network gossip
   * Inside the terminal

   ```
   app_user@bd390faf66db: python gossip_server.py --config ./config/config1.json
   ```

6. Normal node
   * docker run -it --network gossip-network gossip
   * Inside the terminal app_user@bd390faf66db: python gossip_server.py

7.
    * docker rm $(docker ps --filter name=node\* -aq) --> kill the docker dameon running earlier

## Remove all the  containers
```
docker-compose down
```

## Stop all the exited containers
```
docker stop $(docker ps --filter status=running -q)
```





```
sudo docker exec -u root -it monitor-node /bin/bash
python Monitoring_Node.py --config config/monitor.json
```

```
sudo docker exec -it provider-node /bin/bash
python Provider_Node.py --config config/provider.json --version random
```

```
sudo docker exec -u root -it node1 /bin/bash
python gossip_server.py --config config/config1.json

```

```
sudo docker exec -u root -it node2 /bin/bash
python gossip_server.py --config config/config2.json
```


```
sudo docker exec -u root -it gossiprpc_node_3 /bin/bash
python gossip_server.py 
```

```
sudo docker exec -u root -it gossiprpc_node_4 /bin/bash
python gossip_server.py 
```

```
docker exec -u root -it gossiprpc_node_5 /bin/bash
python gossip_server.py
```

```
docker exec -u root -it gossiprpc_node_6 /bin/bash
python gossip_server.py
```

```
docker exec -u root -it gossiprpc_node_7 /bin/bash
python gossip_server.py
```


```
docker exec -u root -it gossiprpc_node_8 /bin/bash
python gossip_server.py
```