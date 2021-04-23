import os
from rpc import XMLRPCGossipManager
from configuration_manager import ConfigurationManager
import sched
import time
import threading
import argparse
import random
import sched
import json
import threading
import Constants
from random_open_port import random_port
import xmlrpc.client
from utils import *

monitor_client =  xmlrpc.client.ServerProxy('http://' + Constants.MONITOR_ADDRESS + '/RPC2')
provider_node =  xmlrpc.client.ServerProxy('http://' + Constants.PROVIDER_ADDRESS + '/RPC2')

scheduler = sched.scheduler(time.time, time.sleep)
# gossip_version = 

def start_gossip_node(gossip_node):
    XMLRPCGossipManager.start_server(gossip_node)


def stop_gossip_node():
    XMLRPCGossipManager.stop_server()


def get_arguments():
    global gossip_version
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',
                        required=False,
                        action='store',
                        dest='config',
                        help='Location to configuration file.',
                        type=str)

    # parser.add_argument('--version',
    #                     required=False,
    #                     action='store',
    #                     dest='version',
    #                     help='Type of Gossip Protocol',
    #                     type=str)


    results = parser.parse_args()
    configuration_file = results.config
    # gossip_version = results.version
    # return configuration_file, bootstrap_server, server_id, no_hash
    return configuration_file

def stabilize_call(node):
    node.updateHearbeat()
    # send heartbeat to monitor
    monitor_client.setheartbeatTime(node.ip)
    scheduler.enter(Constants.WAIT_SECONDS_HEARTBEAT, Constants.HEARTBEAT_PRIO, stabilize_call, (node,))


def scheduleGossip(node):
    # print('\nscheduling gossip')
    node.startGossip(Constants.RANDOM_GOSSIP)
    node.gossip_version = Constants.RANDOM
    # node.startGossip(Constants.RR_GOSSIP)
    # node.startGossip(Constants.BRR_GOSSIP)
    # node.startGossip(Constants.SCRR_GOSSIP)
    # node.gossip_version = Constants.ROUND_ROBIN
    # node.gossip_protocol = Constants.SCRR_GOSSIP
    
    # send end point state map to the monitoring node only when
    # it has done handshake with all live  nodes
    if len(node.live_nodes) == len(node.endpoint_state_map):
        monitor_client.sendEpStateMap(node.ip, node.endpoint_state_map, node.message_count)

    flag_fault = False
    for k,v in node.endpoint_state_map.items():
        if k != node.ip:
            deltatime = getDiffInSeconds(v['last_updated_time'])
            # print('**---++++++ diff:', deltatime)
            if(deltatime >= Constants.WAIT_SECONDS_FAIL):
                flag_fault = True

                node.fault_vector[k] = 1
    
    if flag_fault:
        monitor_client.updateSuspectMatrix(node.ip, node.fault_vector, node.heart_beat_state["generation"])
    
    scheduler.enter(Constants.WAIT_SECONDS_GOSSIP, Constants.GOSSIP_PRIO, scheduleGossip, (node,))


if __name__ == "__main__":

    # configuration_file, bootstrap_server, server_id, no_hash = get_arguments()
    configuration_file = get_arguments()
    from egnode import Node
    import socket
    if configuration_file == None:
        server_ip =  socket.gethostbyname(socket.gethostname()) #"localhost"
        server_port = 5000
        data = {"host": server_ip, "port": server_port, "seed_host": 'node1', "seed_port": 5000}
        with open('config_'+str(server_port), 'w') as outfile:
            json.dump(data, outfile)
        os.environ["GOSSIP_CONFIG"] = 'config_'+str(server_port)
    else:
        os.environ["GOSSIP_CONFIG"] = configuration_file
        ConfigurationManager.reset_configuration()

        server_ip =  socket.gethostbyname(socket.gethostname())#ConfigurationManager.get_configuration().get_gossip_host()
        server_port = ConfigurationManager.get_configuration().get_gossip_port()
    
    server_id = random.randint(1, 1000)
    node = Node(server_ip, server_port, server_id)

    start_gossip_node(node)
    
    # register this node to monitoring node
    monitor_client.setMapping(str(server_ip)+':'+str(server_port))
    provider_node.setMapping(str(server_ip)+':'+str(server_port))
    monitor_client.sendEpStateMap(node.ip, node.endpoint_state_map, node.message_count)
    flag = 0
    scheduler.enter(Constants.WAIT_SECONDS_HEARTBEAT, Constants.HEARTBEAT_PRIO, stabilize_call, (node,))
    stabilization_thread = threading.Thread(target=scheduler.run, args=(True,))
    stabilization_thread.start()

    while True:
        
        console_input = input("\n1.connect\n2.consensus")
        
        if console_input.strip() == "stop":
        
            stop_gossip_node()
            break

        if console_input.strip() == "connect":
            flag = 1
            inp = str(ConfigurationManager.get_configuration().get_seed_host())+':'+str(ConfigurationManager.get_configuration().get_seed_port())
            node.sendSYN(inp)
            scheduler.enter(Constants.WAIT_SECONDS_GOSSIP, Constants.GOSSIP_PRIO, scheduleGossip, (node,))

        if console_input.strip() == "consensus":
            start_measuring(node)