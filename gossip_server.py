# done

import os
from rpc import XMLRPCChordServerManager
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



scheduler = sched.scheduler(time.time, time.sleep)


def start_chord_node(chord_node):
    XMLRPCChordServerManager.start_server(chord_node)


def stop_chord_node():
    XMLRPCChordServerManager.stop_server()


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
    node.startGossip(Constants.RANDOM_GOSSIP)
    scheduler.enter(5, 2, scheduleGossip, (node,))

if __name__ == "__main__":

    # configuration_file, bootstrap_server, server_id, no_hash = get_arguments()
    configuration_file = get_arguments()
    from egnode import Node
    if configuration_file == None:
        server_ip = "localhost"
        server_port = random_port()
        data = {"host": server_ip, "port": server_port, "seed_host": 'localhost', "seed_port": 5001}
        with open('config_'+str(server_port), 'w') as outfile:
            json.dump(data, outfile)
        os.environ["GOSSIP_CONFIG"] = 'config_'+str(server_port)
    else:
        os.environ["GOSSIP_CONFIG"] = configuration_file
        ConfigurationManager.reset_configuration()

        server_ip = ConfigurationManager.get_configuration().get_gossip_host()
        server_port = ConfigurationManager.get_configuration().get_gossip_port()
    
    server_id = random.randint(1, 1000)
    node = Node(server_ip, server_port, server_id)

    start_chord_node(node)
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

        print("\n\nRunning with server id : " + str(server_id))
        console_input = input("1. \"stop\" to shutdown chord node\n2. \"contact\" to contact one of the node\n"
                              "Enter your input:")
        
        if console_input.strip() == "stop":
            stop_chord_node()
            break

        if console_input.strip() == "contact":
            flag = 1
            # pass
            #contact_ip = input("Enter ip/host of node to contact")
            #contact_port = input("Enter port of node to contact")

            #node.contact_node(contact_ip, contact_port)
            inp = str(ConfigurationManager.get_configuration().get_seed_host())+':'+str(ConfigurationManager.get_configuration().get_seed_port())
            node.sendSYN(inp)
            scheduler.enter(5, 2, scheduleGossip, (node,))
            # node.sendACK2()

