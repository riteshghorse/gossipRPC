from xmlrpc.server import SimpleXMLRPCServer
from collections import defaultdict
from gossip_server import get_arguments, start_gossip_node, stop_gossip_node
from configuration_manager import ConfigurationManager
import os
import time
import copy
from utils import *
import Constants
import socket

class ProviderNode:
    def __init__(self):
        self.node_index = 0
        self.IP_to_Node_Index = {}
        self.Index_to_IP = {}
        self.gossip_protocol = ""

    def setMapping(self,ip):
        def typeOfGossip(gossip_protocol):
            gossip_protocol = gossip_protocol.upper()
            if(gossip_protocol == "RANDOM"):
                return Constants.RANDOM_GOSSIP
            elif gossip_protocol == "RR":
                return Constants.RR_GOSSIP
            elif gossip_protocol == "BRR":
                return Constants.BRR_GOSSIP
            elif gossip_protocol == "SCRR":
                return Constants.SCRR_GOSSIP
            else:
                return Constants.RANDOM_GOSSIP

        if ip in self.IP_to_Node_Index:
            return typeOfGossip(self.gossip_protocol)
        
        self.IP_to_Node_Index[ip] = self.node_index
        self.Index_to_IP[self.node_index] = ip
        self.node_index += 1
        return typeOfGossip(self.gossip_protocol)

    def getMapping(self):
        return list(self.IP_to_Node_Index.keys())


    

if __name__ == "__main__":


    configuration_file, gossip_protocol = get_arguments()
   

    os.environ["GOSSIP_CONFIG"] = configuration_file
    ConfigurationManager.reset_configuration()

    server_ip = ConfigurationManager.get_configuration().get_gossip_host()
    server_port = ConfigurationManager.get_configuration().get_gossip_port()
    
    
    node = ProviderNode()
    node.gossip_protocol = gossip_protocol
    start_gossip_node(node)
    print("----------Provider Node---------")
    while 1:
        pass