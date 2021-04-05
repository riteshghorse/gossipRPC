# done

import os
from rpc import XMLRPCChordServerManager
from configuration_manager import ConfigurationManager
import sched
import time
import threading
import argparse
import random
# import time




def start_chord_node(chord_node):
    XMLRPCChordServerManager.start_server(chord_node)


def stop_chord_node():
    XMLRPCChordServerManager.stop_server()


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',
                        required=True,
                        action='store',
                        dest='config',
                        help='Location to configuration file.',
                        type=str)

    # parser.add_argument('--bootstrap-server',
    #                     required=False,
    #                     default=None,
    #                     dest='bootstrap_server',
    #                     help='Bootstrap server in the form (localhost:5000).',
    #                     type=str)

    # parser.add_argument('--server-id',
    #                     required=False,
    #                     action='store',
    #                     dest='server_id',
    #                     help='Server id on chord node. Use this only for testing purpose.',
    #                     type=int)

    # parser.add_argument('--no-hash',
    #                     required=False,
    #                     default=False,
    #                     action='store_true',
    #                     dest='no_hash',
    #                     help='If provided requires keys to be stored to be numeric.'
    #                          'No hashing is performed on keys.')

    results = parser.parse_args()
    configuration_file = results.config
    # bootstrap_server = results.bootstrap_server
    # server_id = results.server_id
    # no_hash = results.no_hash

    # return configuration_file, bootstrap_server, server_id, no_hash
    return configuration_file

if __name__ == "__main__":

    # configuration_file, bootstrap_server, server_id, no_hash = get_arguments()
    configuration_file = get_arguments()
    os.environ["GOSSIP_CONFIG"] = configuration_file
    ConfigurationManager.reset_configuration()

    from egnode import Node
    
    server_ip = ConfigurationManager.get_configuration().get_gossip_host()
    server_port = ConfigurationManager.get_configuration().get_gossip_port()
    server_id = random.randint(1, 1000)
    node = Node(server_ip, server_port, server_id)

    start_chord_node(node)

    while True:
        #time.sleep(5)
        #node.sendSYN()
        print("\n\nRunning with server id : " + str(server_id))
        console_input = input("1. \"stop\" to shutdown chord node\n2. \"contact\" to contact one of the node\n"
                              "Enter your input:")
        
        if console_input.strip() == "stop":
            stop_chord_node()
            break

        if console_input.strip() == "contact":
            #contact_ip = input("Enter ip/host of node to contact")
            #contact_port = input("Enter port of node to contact")

            #node.contact_node(contact_ip, contact_port)
            node.sendSYN()

