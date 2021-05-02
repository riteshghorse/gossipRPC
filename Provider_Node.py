from xmlrpc.server import SimpleXMLRPCServer
from collections import defaultdict
from gossip_server import get_arguments, start_gossip_node, stop_gossip_node
from gossip_rpc.config import Configuration
import os
import time
import copy
import socket
from utilities.utils import *
import utilities.Constants as Constants
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
    import socket
    import socket, dns.resolver,dns.reversename
    configuration_file, gossip_protocol = get_arguments()
   

    os.environ["GOSSIP_CONFIG"] = configuration_file
    configuration = Configuration(configuration_file)    
    host_ip =  socket.gethostbyname(socket.gethostname())
    server_ip = str(dns.resolver.resolve_address(host_ip).rrset[0]).split('.')[0]
    server_port = configuration.get_gossip_port()
    
    
    node = ProviderNode()
    node.gossip_protocol = gossip_protocol
    start_gossip_node(node)
    print("----------Provider Node---------")
    while 1:
        pass