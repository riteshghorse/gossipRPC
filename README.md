# Fault Detection in Distributed Systems using Gossip Protocols

## Developed by: [Ritesh Ghorse](https://github.com/riteshghorse), [Shreyas Muralidhara](https://github.com/shreyas-muralidhara), [Tanvi Pandit](https://github.com/tunveyyy)

- This project is an implementation of 4 Gossip protocols for failure detection in distributed system: Random Gossip, Round Robin Gossip, Binary Round Robin Gossip, Sequence Check Round Robin.

- Implementation is in Python3.

- XMLRPC is used for communication.

- Each docker container serve as a different node.



## Module Developers
1. XMLRPC setup: Ritesh Ghorse
2. 3- way handshake  - Shreyas Muralidhara
3. Random Gossip - Tanvi Pandit
4. Binary Round Robin - Ritesh Ghorse
5. Round Robin and Sequence Check Round Robin: Shreyas Muralidhara
6. Monitoring Node: Ritesh Ghorse
7. Provider Node: Shreyas Muralidhara
8. Docker Containers: Tanvi Pandit
9. Flask app: Tanvi Pandit
10. Test Cases: Each of ous tested our implemented protocols. Sequence Check was divided evenly for test cases.



## Sample commands for running 8-node system
```
docker exec -u root -it monitor-node /bin/bash
python Monitoring_Node.py --config config_files/monitor.json
```

```
docker exec -it provider-node /bin/bash
python Provider_Node.py --config config_files/provider.json --version random
```

```
docker exec -u root -it node1 /bin/bash
python gossip_server.py --config config_files/config1.json

```

```
docker exec -u root -it node2 /bin/bash
python gossip_server.py --config config_files/config2.json
```


```
docker exec -u root -it gossiprpc_node_3 /bin/bash
python gossip_server.py 
```

```
docker exec -u root -it gossiprpc_node_4 /bin/bash
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

### Test Case 1: Single Node Failure
- Terminate one node by hitting "Ctrl+C" on one of the running node.
- Immideately enter 1 on the Monitoring Node terminal.
- It will write out the results in "results.txt" file once it reaches consensus.


### Test Case 2: Single Node Failure
- Terminate two nodes simultaneously by hitting "Ctrl+C" on two of the running nodes.
- Immideately enter 2 on the Monitoring Node terminal.
- It will write out the results in "results.txt" file once it reaches consensus.


### Test Case 3: Dead Node becomes Alive
- Start the previously terminated node again.
- Immideately enter 3 on the Monitoring Node terminal.
- It will write out the results in "results.txt" file once it reaches consensus.



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
