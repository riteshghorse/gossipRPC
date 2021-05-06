# Authors: Shreyas M, Ritesh G, Tanvi P

#Starting point for the nodes. Implementation for starting, stopping and scheduling gossip as well as registering other nodes is written.
#Done via XML RPC


import os
from gossip_rpc.rpc_config import XMLRPCGossipManager
from gossip_rpc.config import Configuration
import sched
import time
import threading
import argparse
import random
import sched
import json
import threading
import utilities.Constants as Constants

import copy
from random_open_port import random_port
import xmlrpc.client
from utilities.utils import *

# definition of Monitoring Node connection
monitor_client =  xmlrpc.client.ServerProxy('http://' + Constants.MONITOR_ADDRESS + '/RPC2')

# definition of Provider Node connection
provider_node =  xmlrpc.client.ServerProxy('http://' + Constants.PROVIDER_ADDRESS + '/RPC2')


scheduler = sched.scheduler(time.time, time.sleep)


def start_gossip_node(gossip_node):
    """
    Author: Ritesh G
    :param gossip_node: Object of Node Class. 

    Makes the Node class object runnable on RPC.
    """
    XMLRPCGossipManager.start_server(gossip_node)


def stop_gossip_node():
    """
    Author: Ritesh G

    Stops the existing node.
    """
    XMLRPCGossipManager.stop_server()


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',
                        required=False,
                        action='store',
                        dest='config',
                        help='Location to configuration file.',
                        type=str)

    parser.add_argument('--version',
                        required=False,
                        action='store',
                        dest='version',
                        help='Type of Gossip Protocol',
                        type=str)


    results = parser.parse_args()
    configuration_file = results.config
    gossip_protocol = results.version
    return (configuration_file, gossip_protocol)

def stabilize_call(node):
    """
    Authors: Shreyas M
    """
    node.updateHearbeat()
    # send heartbeat to monitor
    monitor_client.setheartbeatTime(node.ip)
    scheduler.enter(Constants.WAIT_SECONDS_HEARTBEAT, Constants.HEARTBEAT_PRIO, stabilize_call, (node,))


def scheduleGossip(node):
    """
    Authors: Shreyas M
    """
    node.startGossip(node.gossip_protocol)
    # send end point state map to the monitoring node only when
    # it has done handshake with all live  nodes
    if len(node.live_nodes) == len(node.endpoint_state_map):
        monitor_client.sendEpStateMap(node.ip, node.endpoint_state_map, node.message_count)

    flag_fault = False
    localStateMap = copy.deepcopy(node.endpoint_state_map)
    for k,v in localStateMap.items():
        if k != node.ip:
            deltatime = getDiffInSeconds(v['last_updated_time'])
            if(deltatime >= Constants.WAIT_SECONDS_FAIL):
                flag_fault = True
                node.fault_vector[k] = 1

    if flag_fault:
        monitor_client.updateSuspectMatrix(node.ip, node.fault_vector, node.heart_beat_state["generation"])
    
    scheduler.enter(Constants.WAIT_SECONDS_GOSSIP, Constants.GOSSIP_PRIO, scheduleGossip, (node,))


def registerNode(server_ip, server_port, node):
    """
    Author: Ritesh G

    :param server_ip  : Node's IP address
    :param server_port: Node's Port 
    :param node       : Object of Node class

    Registers a node to the Monitoring Node and Provider Node.
    Sets the gossip protocol for current Node as suggested by the Provider Node.
    """
    monitor_client.setMapping(str(server_ip)+':'+str(server_port))
    node.gossip_protocol = provider_node.setMapping(str(server_ip)+':'+str(server_port))
    if(node.gossip_protocol == Constants.RANDOM_GOSSIP):
        node.gossip_version = Constants.RANDOM
    else:
        node.gossip_version = Constants.ROUND_ROBIN

    monitor_client.sendEpStateMap(node.ip, node.endpoint_state_map, node.message_count)


def scheduleHeartbeat(node):
    """
    Author: Shreyas M
    """
    scheduler.enter(Constants.WAIT_SECONDS_HEARTBEAT, Constants.HEARTBEAT_PRIO, stabilize_call, (node,))
    stabilization_thread = threading.Thread(target=scheduler.run, args=(True,))
    stabilization_thread.start()

if __name__ == "__main__":

    configuration_file, _ = get_arguments()
    import socket, dns.resolver, dns.reversename
    from egnode import Node

    if configuration_file == None:
        host_ip =  socket.gethostbyname(socket.gethostname())
        server_ip = str(dns.resolver.resolve_address(host_ip).rrset[0]).split('.')[0]
        server_port = 5000
        data = {"host": server_ip, "port": server_port, "seed_host": "node1", "seed_port": 5000}
        with open('config_'+str(server_port), 'w') as outfile:
            json.dump(data, outfile)
        os.environ["GOSSIP_CONFIG"] = 'config_'+str(server_port)
        configuration = Configuration(os.environ["GOSSIP_CONFIG"])
    else:
        os.environ["GOSSIP_CONFIG"] = configuration_file
        configuration = Configuration(os.environ["GOSSIP_CONFIG"])
        # ConfigurationManager.reset_configuration()
        host_ip =  socket.gethostbyname(socket.gethostname())
        server_ip = str(dns.resolver.resolve_address(host_ip).rrset[0]).split('.')[0]
        print(server_ip)
        # server_port = ConfigurationManager.get_configuration().get_gossip_port()
        server_port = configuration.get_gossip_port()
    
    server_id = random.randint(1, 1000)
    node = Node(server_ip, server_port, server_id)

    # register node to be used in RPC
    start_gossip_node(node)
    
    # register this node to monitoring node
    registerNode(server_ip, server_port, node)
    
    # schedule heartbeat
    scheduleHeartbeat(node)

    if configuration_file == None:
        inp = str(configuration.get_seed_host())+':'+str(configuration.get_seed_port())
        node.sendSYN(inp)
        scheduler.enter(Constants.WAIT_SECONDS_GOSSIP, Constants.GOSSIP_PRIO, scheduleGossip, (node,))

    else:
        while True:
            
            console_input = input("\n1.connect\n2.stop\n3.collect")
            
            if console_input.strip() == "stop":
                stop_gossip_node()
                break

            if console_input.strip() == "connect":
                flag = 1
                inp = str(configuration.get_seed_host())+':'+str(configuration.get_seed_port())
                node.sendSYN(inp)
                scheduler.enter(Constants.WAIT_SECONDS_GOSSIP, Constants.GOSSIP_PRIO, scheduleGossip, (node,))
            
            if console_input.strip() == "collect":
                import json
                with open('digestList.json', 'w') as fp:
                    json.dump(node.gDigestList, fp)
            

