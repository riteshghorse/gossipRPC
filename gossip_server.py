# done

import os
from rpc import XMLRPCGossipManager
from configuration_manager import ConfigurationManager
import sched
import time
import threading
import argparse
import random
import sched
# import time
import json
import threading
import Constants
from random_open_port import random_port
from RepeatedTimer import RepeatedTimer
import xmlrpc.client
from utils import *

monitor_client =  xmlrpc.client.ServerProxy('http://' + Constants.MONITOR_ADDRESS + '/RPC2')
scheduler = sched.scheduler(time.time, time.sleep)
# proxy = xmlrpc.client.ServerProxy("http://localhost:8000/") 
# cket.gethostbyname(hostname)
def start_gossip_node(gossip_node):
    XMLRPCGossipManager.start_server(gossip_node)


def stop_gossip_node():
    XMLRPCGossipManager.stop_server()


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',
                        required=False,
                        action='store',
                        dest='config',
                        help='Location to configuration file.',
                        type=str)



    results = parser.parse_args()
    configuration_file = results.config

    # return configuration_file, bootstrap_server, server_id, no_hash
    return configuration_file

def stabilize_call(node):
    node.updateHearbeat()
    scheduler.enter(1, 1, stabilize_call, (node,))


def scheduleGossip(node):
    # print('\nscheduling gossip')
    # node.startGossip(Constants.RANDOM_GOSSIP)
    node.startGossip(Constants.RR_GOSSIP)
    flag_fault = False
    for k,v in node.endpoint_state_map.items():
        if k != node.ip:
            deltatime = getDiffInSeconds(v['last_updated_time'])
            # print('**---++++++ diff:', deltatime)
            if(deltatime >= Constants.WAIT_SECONDS_FAIL):
                flag_fault = True

                node.fault_vector[k] = 1
                # print(node.fault_vector)    
                # monitor_client.
    
    if flag_fault:
        monitor_client.updateSuspectMatrix(node.ip, node.fault_vector, node.heart_beat_state["generation"])
    # send end point state map to the monitoring node only when
    # it has done handshake with all live  nodes
    # print('***************** before sending epstate map ******************')
    # print(node.live_nodes, len(node.endpoint_state_map))
    if len(node.live_nodes) == len(node.endpoint_state_map):
        # print('***************** sent epstate map ******************')
        # print(node.message_count)
        monitor_client.sendEpStateMap(node.ip, node.endpoint_state_map, node.message_count)
    
    scheduler.enter(5, 2, scheduleGossip, (node,))


# def start_measuring(node):
#     node.


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

    flag = 0
    scheduler.enter(1, 1, stabilize_call, (node,))
    stabilization_thread = threading.Thread(target=scheduler.run, args=(True,))
    stabilization_thread.start()
    #update heartbeat every 1 sec
    # happens internally
    # node.updateHearbeat()
    # rt = RepeatedTimer(1, node.updateHearbeat())
    # threading.Timer(Constants.WAIT_SECONDS_HEARTBEAT, node.updateHearbeat()).start()
    while True:
        # time.sleep(5)
        # node.sendSYN()

        # while flag:

        # t = threading.Timer(Constants.WAIT_SECONDS_HEARTBEAT, node.updateHearbeat()).start()

        console_input = input("\n1.connect\n2.consensus")
        
        if console_input.strip() == "stop":
        
            stop_gossip_node()
            break

        if console_input.strip() == "connect":
            flag = 1
            # pass
            #contact_ip = input("Enter ip/host of node to contact")
            #contact_port = input("Enter port of node to contact")

            #node.contact_node(contact_ip, contact_port)
            inp = str(ConfigurationManager.get_configuration().get_seed_host())+':'+str(ConfigurationManager.get_configuration().get_seed_port())
            node.sendSYN(inp)
            scheduler.enter(5, 2, scheduleGossip, (node,))
            # node.sendACK2()

        if console_input.strip() == "consensus":
            start_measuring(node)