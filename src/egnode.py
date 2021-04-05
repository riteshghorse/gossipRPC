# done

import xmlrpc.client
from SynGossipDigest import *
from SynVerbHandler import *
import Constants
from utils import getCurrentGeneration
from configuration_manager import ConfigurationManager


class Node(object):

    def __init__(self, host, port, id):
        

        self.heart_beat_state = {"heartBeatValue": Constants.INITIAL_HEARTBEAT, "generation": getCurrentGeneration()} 
        self.app_state = {"IP_Port": str(host)+str(port) , "App_version": Constants.APP_VERSION_DEFAULT, "App status": Constants.STATUS_NORMAL}
        self.endpoint_state_map = {self.app_state["IP_Port"]: {'heartBeat': [self.heart_beat_state['heartBeatValue'], self.heart_beat_state['generation']]}}
        self.gDigestList = {self.app_state['IP_Port'] : [self.app_state['App_version'], self.heart_beat_state['generation'], self.heart_beat_state['heartBeatValue']]} 
        #{IP_Port:{'heartBeat':[version, generation], 'appState':[], 'last_msg_received': time}}
        
        
        self.fault_vector = list()   
        self.live_nodes = set()
        self.dead_nodes = set()

    def sendSYN(self):
        """
        sends SYN. Starts gossiping

        Note: If only one node is present in gDigestList
        """
        synDigest = SynGossipDigest(Constants.DEFAULT_CLUSTER, self.gDigestList)
        if len(self.gDigestList) == 1:
            if ConfigurationManager.get_configuration().getConfigFile() == 'config/config1.json':
                sendTo = 'localhost:5002'
            else:
                sendTo = 'locahost:5001'

        else:
            sendTo = 'localhost:5001'   #TODO: change it to random

        print('--------'+sendTo)
        client =  xmlrpc.client.ServerProxy('http://' + sendTo + '/RPC2')
        client.acceptSyn(synDigest)
        print("SYN sent")

    def acceptSyn(self,synDigest):
        variable = SynVerbHandler()
        deltaGDigest, deltaEpStateMap = variable.handleSync(synDigest)
        print('\nSyn handler completed')
        print('DIgest contains: ', deltaGDigest)

    def get_id_of_node(self, calling_id):
        print("Calling {} from {}.".format(self.id, calling_id))
        return self.id


    def contact_node(self, host, port):
        client =  xmlrpc.client.ServerProxy('http://' + host + ":" + str(port) + '/RPC2')
        contact_node_id = client.get_id_of_node(self.id)
        print("Contact node with id: {}".format(contact_node_id))