# Authors: Shreyas M, Ritesh G, Tanvi P

import copy
import datetime
import math
import threading
import xmlrpc.client
from random import sample

import utilities.Constants as Constants
from handlers.SynGossipDigest import *
from handlers.SynVerbHandler import *
from handlers.AckVerbHandler import *
from handlers.Ack2VerbHandler import *
from utilities.utils import *


 
monitor_client =  xmlrpc.client.ServerProxy('http://' + Constants.MONITOR_ADDRESS + '/RPC2', allow_none=True)
provider_node =  xmlrpc.client.ServerProxy('http://' + Constants.PROVIDER_ADDRESS + '/RPC2', allow_none=True)

class Node(object):

    def __init__(self, host, port, id):
        """
        Author: Ritesh G

        Initialization of Data Structures maintained at every node.

        """
        self.ip = str(host) + ':' + str(port)
        self.heart_beat_state = {"heartBeatValue": Constants.INITIAL_HEARTBEAT, "generation": getCurrentGeneration()} 
        self.app_state = {"IP_Port": str(host)+':'+str(port) , "App_version": Constants.APP_VERSION_DEFAULT, "App_status": Constants.STATUS_NORMAL}
        self.endpoint_state_map = {self.app_state["IP_Port"]: {'heartBeat': self.heart_beat_state, 'appState':self.app_state, 'last_updated_time': getTimeStamp()}}
        self.gDigestList = {self.app_state['IP_Port'] : [self.app_state['App_version'], self.heart_beat_state['generation'], self.heart_beat_state['heartBeatValue']]} 
                
        self.fault_vector = {self.ip:0}  
        self.live_nodes = list(self.ip)
        self.dead_nodes = list()
        self.handshake_nodes = list()
        self.message_count = 0
        self.rr_index = 0
        self.rr_list = []
        self.gossip_version = 0
        self.rr_round = 0
        self.gossip_protocol= ""
        self.sc_index = ""    # used in sc round robin for current ip position
        self.lastReceived = {'ip': "", 'timestamp': ""}

    def updateHearbeat(self):
        self.heart_beat_state["heartBeatValue"] += 1
        self.endpoint_state_map[self.ip]['heartBeat'] = self.heart_beat_state
        self.gDigestList[self.ip][2] = self.heart_beat_state['heartBeatValue'] 
        

    def sendSYN(self, sendTo):
        """
        Author: Shreyas M
        
        :param sendTo: IP address of node to initiate the handshake.

        First step of handshake. Sends SYN.
        """
        self.message_count += 1
        synDigest = SynGossipDigest(Constants.DEFAULT_CLUSTER, self.gDigestList)
        try:
            client =  xmlrpc.client.ServerProxy('http://' + sendTo + '/RPC2')
            client.acceptSyn(synDigest, self.ip)
            print("SYN sent")
        except Exception as e:
            pass
        

    def acceptSyn(self,synDigest, clientIp):
        """
        Author: Shreyas M

        :param synDigest: List of IPs that the sender knows
        :param clientIP: sender IP

        Sends out the accept ACK along with delta list of nodes it needs the endpoint state map of.
        
        """
        self.message_count += 1
        variable = SynVerbHandler(self)
        deltaGDigest, deltaEpStateMap = variable.handleSync(synDigest)
        print('\nSyn handler completed')
        try:
            client =  xmlrpc.client.ServerProxy('http://' + clientIp + '/RPC2')
            client.acceptAck(deltaGDigest, deltaEpStateMap, self.app_state["IP_Port"])
            print('\nACK sent')
        except Exception as e:
            pass

    def updateTimestamp(self, ip):
        try:
            self.endpoint_state_map[ip]['last_updated_time'] = getTimeStamp()
        except Exception as e:
            pass
        
        # if ip in self.fault_vector and self.fault_vector[ip] == 1:
        self.fault_vector[ip] = 0
        
        try:
            # print(self.ip, self.fault_vector)
            monitor_client.updateSuspectMatrix(self.ip, self.fault_vector, self.getGeneration(ip))
        except Exception as e:
            pass

    def updateAliveStatus(self, ip, clientIp):
        if(self.gossip_protocol == Constants.SCRR_GOSSIP):
            if(ip not in self.fault_vector or ((self.fault_vector[ip]!=1) or (self.fault_vector[ip]==1 and ip==clientIp))):
                self.updateTimestamp(ip)
        else:
            self.updateTimestamp(ip)


    def acceptAck(self, deltaGDigest, deltaEpStateMap, clientIp):
        """
        Author: Shreyas M

        :param deltaGDigest: List of IPs for which client needs the endpoint State map 
        :param deltaEpStateMap: List of endpoint statemap of IPs that I don't know.
        :param clientIP: sender IP
        
        Sends back the endpoint statempa of the requested IPs
        """
        print('\nIn Accept ACK')
        self.message_count += 1
        epStateMap = {}

        ackHandler = AckVerbHandler(self)
        # retrieve meta-app states of requested IPs
        epStateMap = ackHandler.setEpStateMap(deltaGDigest)
        

        #update my own meta-apps in endpoint
        ackHandler.updateEpStateMap(deltaEpStateMap, clientIp)
         
        self.fault_vector[clientIp] = 0
        try:
            # print(self.ip, self.fault_vector)
            monitor_client.updateSuspectMatrix(self.ip, self.fault_vector, self.getGeneration(clientIp))
            self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()
        except Exception as e:
            pass
        # updating timestamp for clientIp
        if clientIp in self.endpoint_state_map:
            self.updateAliveStatus(clientIp, clientIp)



        print("\nACK handled... sending ACK2")
        
        if not self.isInHandshake(clientIp):
            self.handshake_nodes.append(clientIp)

        if not self.isInLivenodes(clientIp):
            self.live_nodes = list(self.endpoint_state_map.keys())  
        
        try:
            client =  xmlrpc.client.ServerProxy('http://' + clientIp + '/RPC2')
            client.acceptAck2(epStateMap, self.app_state["IP_Port"])
            print("\nACK2 sent")
        except Exception as e:
            pass


    def acceptAck2(self, deltaEpStateMap, clientIp):
        """
        Author: Shreyas M

        :param deltaEpStateMap: List of endpoint statemap of IPs that I don't know.
        :param clientIP: sender IP

        Updates my own end point statemap as suggested by client IP
        
        """
        print('\n in Accept Ack 2')
        self.message_count += 1

        ack2Handler = Ack2VerbHandler(self)
        ack2Handler.updateEpStateMap(deltaEpStateMap, clientIp)
        
        if not self.isInHandshake(clientIp):
            self.handshake_nodes.append(clientIp)
            
        if not self.isInLivenodes(clientIp):
            self.live_nodes = list(self.endpoint_state_map.keys())

        self.fault_vector[clientIp] = 0
        try:
            # print(self.ip, self.fault_vector)
            monitor_client.updateSuspectMatrix(self.ip, self.fault_vector, self.getGeneration(clientIp))
            self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()
        except Exception as e:
            pass
        # updating timestamp of clientIp
        self.updateAliveStatus(clientIp, clientIp)
        print('\n ACK2 processed... complete handshake')



    def getGeneration(self, clientIp):
        if clientIp in self.endpoint_state_map:
            return self.endpoint_state_map[clientIp]["heartBeat"]["generation"]
        else:
            return getCurrentGeneration()

    def isInHandshake(self, ip):
        if ip in self.handshake_nodes:
            return True
        else:
            return False

    def isInLivenodes(self, ip):
        if ip in self.live_nodes:
            return True
        else:
            return False

    def initiateRandomGossip(self):
        """
        Author: Tanvi P
        :params None

        Create a copy of the gossipList with each node and randomly select a single node to send gossip.
        Initiate a gossip with the randomly selected node

        """
        digestList = copy.deepcopy(self.gDigestList)

        digestList.pop(self.ip, None)
        from gossip_server import scheduleGossip, scheduler

        keyList = list(digestList.keys() - self.ip)
        random_numbers = sample(range(0, len(keyList)), 1)
        self.message_count += 1
        for i in random_numbers:
        
            ip = keyList[i]
            if self.isInHandshake(ip):
                try:
                    client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                    client.receiveGossip(self.gDigestList, self.ip)
                except Exception as e:
                    pass
            else:
                print('--------------------> sending syn'+ip)
                self.sendSYN(ip)

        

    def initiateRRGossip(self): 
        """
        Author: Shreyas M

        Implementation of Round Robin Gossip Algorithm

        It keeps track of the node list and gossips based on the index of list in each round in round robin fashion.
        rr_index provides the index to gossip in each round

        """
        if self.rr_index == 0:
            self.rr_list = copy.deepcopy(self.gDigestList)
            self.rr_list.pop(self.ip, None)

        print('------ Starting Round Robin Rounds -------')
        

        from gossip_server import scheduleGossip, scheduler

        keyList = list(self.rr_list.keys() - self.ip)

        self.message_count += 1
        ip = keyList[self.rr_index]
        if self.isInHandshake(ip):
            try:
                print("I'm gossiping to--> ", ip)
                client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                client.receiveGossip(self.gDigestList, self.ip)
            except Exception as e:
                pass
        else:
            print('------> Initiate Handshake for: '+ip)
            self.sendSYN(ip)

        # Update to rr_index for the key list based on the round robin algorithm.
        self.rr_index =  (self.rr_index + 1) % len(self.rr_list)

    def initiateBinaryRRGossip(self):     
        """
        Author: Ritesh G

        Implementation of Binary Round Robin Gossip Algorithm.
        It doesn't update the node list that follows the round robin order unless all indexes
        in current list are processed. Special formula is used in calculating destination
        node index.

        Sends a normal gossip if already done with handshake. Else does the handshake first.
        """
        if len(self.rr_list)==0 or self.rr_round-1 > math.log2(len(self.rr_list)):
            self.rr_list = provider_node.getMapping()
            self.rr_index = self.rr_list.index(self.ip) + 1
            self.rr_round = 0
            print('------ Starting Binary Round Robin Rounds -------')

        self.message_count += 1         # used in monitoring node
        ip = self.rr_list[(self.rr_index)%len(self.rr_list)]
        
        if self.isInHandshake(ip):
            try:
                print("I'm gossiping to--> ", ip)
                client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                client.receiveGossip(self.gDigestList, self.ip)
            except Exception as e:
                print(e)
                pass
        else:
            print('------> Initiate Handshake for: '+ip)
            self.sendSYN(ip)
        self.rr_index =  (self.rr_index + 2**(self.rr_round)) % len(self.rr_list)
        self.rr_round += 1


    def initiateSCRRGossip(self):
        """
        Author: Shreyas M

        It keeps track of the node list and gossips based on the index of list in each round in round robin fashion.
        rr_index provides the index to gossip in each round

        On the receive gossip side it expects the gossip from specfic rr_index node if thats not received then it marks 
        the node as potential failure. Shares this information with the monitor node.
        
        """
        if len(self.rr_list)==0 or self.rr_index ==  self.sc_index:
            self.rr_list = provider_node.getMapping()
            self.sc_index = self.rr_list.index(self.ip)
            self.rr_index = (self.sc_index + 1) % len(self.rr_list)

        from gossip_server import scheduleGossip, scheduler
        # Update to rr_index for the rr list from provider based on the round robin algorithm.
        self.rr_round = (self.rr_index - self.sc_index + len(self.rr_list))%len(self.rr_list)
        
        self.message_count += 1
        ip = self.rr_list[self.rr_index]
        if self.isInHandshake(ip):
            try:
                print("I'm gossiping to--> ", ip)
                client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                client.receiveGossip(self.gDigestList, self.ip)
            except Exception as e:
                pass
        else:
            print('------> Initiate Handshake for: '+ip)
            self.sendSYN(ip)
        self.rr_index =  (self.rr_index + 1) % len(self.rr_list)
        



    def startGossip(self, gossip_protocol):
        """
        Author: Tanvi P
        
        Making a single application run multiple protocols via command line argument
        :param gossip_protocol: Type of protocol to run
        :return: returns nothing
        
        """
        if gossip_protocol == Constants.RANDOM_GOSSIP:
            self.initiateRandomGossip()

        elif gossip_protocol == Constants.RR_GOSSIP:
            self.initiateRRGossip()

        elif gossip_protocol == Constants.BRR_GOSSIP:
            self.initiateBinaryRRGossip()

        elif gossip_protocol == Constants.SCRR_GOSSIP:
            self.initiateSCRRGossip()

    def receiveGossip(self, digestList, clientIp):
        """
        Authors: Ritesh G, Shreyas M
        :param digestList:  gossip digest list received from clientIP
        :param clientIp:    IP of sender node
        
        
        RANDOM:             Add the unknown IPs to its own digest list. Update the EndPoint State Map
                            for the IPs which are already in its EndPoint State Map. Update the last_updated_time
                            for the clientIp.

        ROUND_ROBIN:        Perform the same operation as that of RANDOM. In addition to this update the 
                            last_updated_time for the IPs received in digestList which are already in its
                            EndPoint State Map for that round.

        BINARY_ROUND_ROBIN: Same as ROUND_ROBIN.

        SEQUENCE_CHECK:     Same as ROUND_ROBIN. In addition to this, it checks if the it missed any gossip from 
                            a IP in previous round. In this case, it is detected as FAIL.

        """

        print('++++> Gossip received from--> ' + clientIp)
        if self.gossip_protocol == Constants.SCRR_GOSSIP:
            # checks for missed gossip in previous round. 
            # In this case, it is detected as FAIL

            indexOfClient = self.rr_list.index(clientIp)
            lastReceivedIp = self.rr_list[(indexOfClient + 1)%len(self.rr_list)]
            
            if lastReceivedIp != self.ip:
                if(lastReceivedIp != self.lastReceived['ip']) or \
                    (getDiffInSeconds(self.lastReceived['timestamp']) > Constants.WAIT_SECONDS_FAIL):
                    print('Gossip message expected from: '+lastReceivedIp + ' in last round. Hence marking as FAIL')
                    self.fault_vector[lastReceivedIp] = 1
                    monitor_client.updateSuspectMatrix(self.ip, self.fault_vector, self.getGeneration(lastReceivedIp))
        
            self.lastReceived['ip'] = clientIp
            self.lastReceived['timestamp'] = getTimeStamp()

        currenttList = copy.deepcopy(self.gDigestList)
        updatedList = []
        for ip, digest in digestList.items():
            if ip == self.ip:
                continue

            
            if ip in self.gDigestList:
                if self.gDigestList[ip][1] < digest[1]:
                    currenttList[ip] = digest
                    try:
                        self.endpoint_state_map[ip]['appState']['App_version'] = digest[0]
                        self.endpoint_state_map[ip]['heartBeat']['generation'] = digest[1]
                        self.endpoint_state_map[ip]['heartBeat']['heartBeatValue'] = digest[2]
                        updatedList.append(ip)
                    except Exception as e:
                        print('passed the exception')
                        pass            
                elif self.gDigestList[ip][2] < digest[2] and self.gDigestList[ip][1] == digest[1]:
                    currenttList[ip][2] = digest[2]
                    try:
                        self.endpoint_state_map[ip]['heartBeat']['heartBeatValue'] = digest[2]
                        updatedList.append(ip)
                    except Exception as e:
                        print('passed the exception')
                        pass            
                
                    if self.gossip_version == Constants.ROUND_ROBIN:
                        self.updateAliveStatus(ip, clientIp)

            else:
                currenttList[ip] = digest
                   
        print('Status updated by: '+self.ip)
        print('for: ', updatedList)
        print('as directed by: ', clientIp)    

        self.gDigestList = copy.deepcopy(currenttList)

        # updating timestamp for clientIp
        if clientIp in self.endpoint_state_map:
            self.updateAliveStatus(clientIp, clientIp)
