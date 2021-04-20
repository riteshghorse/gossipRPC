from xmlrpc.server import SimpleXMLRPCServer
from collections import defaultdict
from gossip_server import get_arguments, start_gossip_node, stop_gossip_node
from configuration_manager import ConfigurationManager
import os
import time
import copy
from utils import *
import Constants

class ProviderNode:
    def __init__(self):
        self.node_index = 0
        self.IP_to_Node_Index = {}
        self.Index_to_IP = {}

    def setMapping(self,ip):
        if ip in self.IP_to_Node_Index:
            return
        
        self.IP_to_Node_Index[ip] = self.node_index
        self.Index_to_IP[self.node_index] = ip
        self.node_index += 1

    def getMapping(self):
        return list(self.IP_to_Node_Index.keys())


    

if __name__ == "__main__":


    configuration_file = get_arguments()
   

    os.environ["GOSSIP_CONFIG"] = configuration_file
    ConfigurationManager.reset_configuration()

    server_ip = ConfigurationManager.get_configuration().get_gossip_host()
    server_port = ConfigurationManager.get_configuration().get_gossip_port()
    
    
    node = ProviderNode()
    start_gossip_node(node)
    print('Rider-Provider up and running')
    while 1:
        pass