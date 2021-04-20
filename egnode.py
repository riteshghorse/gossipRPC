# done

import xmlrpc.client
from SynGossipDigest import *
from SynVerbHandler import *
import Constants
from utils import getCurrentGeneration, getTimeStamp
from configuration_manager import ConfigurationManager
import datetime
import threading
import copy
from random import sample
import math


monitor_client =  xmlrpc.client.ServerProxy('http://' + Constants.MONITOR_ADDRESS + '/RPC2', allow_none=True)
provider_node =  xmlrpc.client.ServerProxy('http://' + Constants.PROVIDER_ADDRESS + '/RPC2', allow_none=True)

class Node(object):

    def __init__(self, host, port, id):
        self.ip = str(host) + ':' + str(port)

        self.heart_beat_state = {"heartBeatValue": Constants.INITIAL_HEARTBEAT, "generation": getCurrentGeneration()} 
        self.app_state = {"IP_Port": str(host)+':'+str(port) , "App_version": Constants.APP_VERSION_DEFAULT, "App_status": Constants.STATUS_NORMAL}
        self.endpoint_state_map = {self.app_state["IP_Port"]: {'heartBeat': self.heart_beat_state, 'appState':self.app_state, 'last_updated_time': getTimeStamp()}}
        self.gDigestList = {self.app_state['IP_Port'] : [self.app_state['App_version'], self.heart_beat_state['generation'], self.heart_beat_state['heartBeatValue']]} 
        #{IP_Port:{'heartBeat':[version, generation], 'appState':[], 'last_msg_received': time}}
        # print(self.gDigestList)
        
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
        sends SYN. Starts gossiping

        Note: If only one node is present in gDigestList
        """
        self.message_count += 1
        synDigest = SynGossipDigest(Constants.DEFAULT_CLUSTER, self.gDigestList)
        try:
            client =  xmlrpc.client.ServerProxy('http://' + sendTo + '/RPC2')
            client.acceptSyn(synDigest, self.ip)
            print("SYN sent")
        except Exception as e:
            pass
        
        # sendAck2()


    def acceptSyn(self,synDigest, clientIp):
        self.message_count += 1
        variable = SynVerbHandler(self)
        deltaGDigest, deltaEpStateMap = variable.handleSync(synDigest)
        print('\nSyn handler completed')
        # print('DIgest contains: ', (deltaGDigest, self.endpoint_state_map))
        try:
            client =  xmlrpc.client.ServerProxy('http://' + clientIp + '/RPC2')
            client.acceptAck(deltaGDigest, deltaEpStateMap, self.app_state["IP_Port"])
            print('\nACK sent')
        except Exception as e:
            pass
        #TODO: timer for ack expiry

    def updateTimestamp(self, ip):
        try:
            self.endpoint_state_map[ip]['last_updated_time'] = getTimeStamp()
        except Exception as e:
            pass
        
        # if ip in self.fault_vector and self.fault_vector[ip] == 1:
        self.fault_vector[ip] = 0
        
        # print("++++++++++++++", ip)
        try:
            # print('sending ====')
            print(self.ip, self.fault_vector)
            print((self.ip, self.fault_vector, self.getGeneration(ip)))
            monitor_client.updateSuspectMatrix(self.ip, self.fault_vector, self.getGeneration(ip))
        except Exception as e:
            print(e)
            pass
        # print('block completed')

    def updateAliveStatus(self, ip, clientIp):
        # print("-----------------------Within updateAlive status ", self.fault_vector[ip], ip, clientIp)
        if(self.gossip_protocol == Constants.SCRR_GOSSIP):
            
            if(ip not in self.fault_vector or ((self.fault_vector[ip]!=1) or (self.fault_vector[ip]==1 and ip==clientIp))):
                # print('block 1')
                self.updateTimestamp(ip)
        else:
            print('block 2')
            self.updateTimestamp(ip)

    def acceptAck(self, deltaGDigest, deltaEpStateMap, clientIp):
        print('\nin accept ack')
        self.message_count += 1
        epStateMap = {}
        # print((deltaGDigest, deltaEpStateMap, clientIp))

        # retrieve meta-app states of requested IPs
        for ip in deltaGDigest:
            if ip in self.endpoint_state_map:
                epStateMap[ip] = self.endpoint_state_map[ip]
                
        #update my own meta-apps in endpoint

        for ip, epState in deltaEpStateMap.items():
            #update by comparing which has the latest heartbeat
            if ip in self.endpoint_state_map:
                if deltaEpStateMap[ip]["heartBeat"]["heartBeatValue"] > self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"]: 
                    self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                    #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                    self.gDigestList[ip] = [self.endpoint_state_map[ip]['appState']['App_version'], self.endpoint_state_map[ip]['heartBeat']['generation'], self.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
                    if self.gossip_version == Constants.ROUND_ROBIN:
                        # self.endpoint_state_map[ip]['last_updated_time'] = getTimeStamp()
                        self.updateAliveStatus(ip, clientIp)
            else:
                #since i don't know this ip, put entire epState for this ip
                self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                self.gDigestList[ip] = [self.endpoint_state_map[ip]['appState']['App_version'], self.endpoint_state_map[ip]['heartBeat']['generation'], self.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
            
        # print('updated epstate')
        # updating timestamp for clientIp
        if clientIp in self.endpoint_state_map:
            # self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()
            self.updateAliveStatus(clientIp, clientIp)

        print("\nACK handled... sending ack2")
        
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
        print('\n in acceptAck 2')
        self.message_count += 1

        for ip, epState in deltaEpStateMap.items():
            #update by comparing which has the latest heartbeat
            if ip == self.ip:
                continue
            if ip in self.endpoint_state_map:
                if deltaEpStateMap[ip]["heartBeat"]["heartBeatValue"] > self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"]: 
                    self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                    #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                    self.gDigestList[ip] = [self.endpoint_state_map[ip]['appState']['App_version'], self.endpoint_state_map[ip]['heartBeat']['generation'], self.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
                    if self.gossip_version == Constants.ROUND_ROBIN:
                        self.updateAliveStatus(ip, clientIp)
            else:
                #since i don't know this ip, put entire epState for this ip
                self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                self.gDigestList[ip] = [self.endpoint_state_map[ip]['appState']['App_version'], self.endpoint_state_map[ip]['heartBeat']['generation'], self.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
            
            
        if not self.isInHandshake(clientIp):
            self.handshake_nodes.append(clientIp)
            
        if not self.isInLivenodes(clientIp):
            self.live_nodes = list(self.endpoint_state_map.keys())

        # updating timestamp of clientIp
        # self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()
        
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
        digestList = copy.deepcopy(self.gDigestList)

        digestList.pop(self.ip, None)
        from gossip_server import scheduler, scheduleGossip

        keyList = list(digestList.keys() - self.ip)
        random_numbers = sample(range(0, len(keyList)), 1)
        # print('-------------------------------------------------')
        self.message_count += 1
        print(keyList, random_numbers)
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
        if self.rr_index == 0:
            self.rr_list = copy.deepcopy(self.gDigestList)
            self.rr_list.pop(self.ip, None)

        print('-------------')
        print(self.handshake_nodes, self.fault_vector)
        print('-------------')

        from gossip_server import scheduler, scheduleGossip

        print('In round: '+str(self.rr_index))
        keyList = list(self.rr_list.keys() - self.ip)

        self.message_count += 1
        ip = keyList[self.rr_index]
        if self.isInHandshake(ip):
            try:
                client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                client.receiveGossip(self.gDigestList, self.ip)
            except Exception as e:
                pass
        else:
            print('--------------------> sending syn'+ip)
            self.sendSYN(ip)
        self.rr_index =  (self.rr_index + 1) % len(self.rr_list)
        print('round robin ' + str(self.rr_index) + 'done')

    def initiateBinaryRRGossip(self):     
        
        if len(self.rr_list)==0 or len(self.rr_list)==1 or self.rr_round-1 > math.log2(len(self.rr_list)):
            self.rr_list = copy.deepcopy(self.gDigestList)
            self.rr_list.pop(self.ip, None)
            self.rr_index = 0
            self.rr_round = 0

        from gossip_server import scheduler, scheduleGossip

        print('In round: '+str(self.rr_round))
        keyList = list(self.rr_list.keys())
        print('my list-->', keyList)
        self.message_count += 1
        ip = keyList[self.rr_index]
        print("ip i'm sending--> ", ip)
        if self.isInHandshake(ip):
            try:
                client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                client.receiveGossip(self.gDigestList, self.ip)
            except Exception as e:
                print(e)
                pass
        else:
            print('--------------------> sending syn'+ip)
            self.sendSYN(ip)
        self.rr_index =  (self.rr_index + 2**(self.rr_round)) % len(self.rr_list)
        self.rr_round += 1
        print(self.rr_index)
        print('round robin ' + str(self.rr_round) + 'done')


    def initiateSCRRGossip(self):

        if len(self.rr_list)==0 or self.rr_index ==  self.sc_index:
            self.rr_list = provider_node.getMapping()
            self.sc_index = self.rr_list.index(self.ip)
            self.rr_index = (self.sc_index + 1) % len(self.rr_list)

        print('-------------')
        print(self.endpoint_state_map, self.fault_vector)
        print('-------------')

        from gossip_server import scheduler, scheduleGossip
        self.rr_round = (self.rr_index - self.sc_index + len(self.rr_list))%len(self.rr_list)
        print('In round: '+str(self.rr_round))
        
        self.message_count += 1
        ip = self.rr_list[self.rr_index]

        if self.isInHandshake(ip):
            try:
                client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                client.receiveGossip(self.gDigestList, self.ip)
            except Exception as e:
                pass
        else:
            print('--------------------> sending syn'+ip)
            self.sendSYN(ip)
        self.rr_index =  (self.rr_index + 1) % len(self.rr_list)
        print('round robin ' + str(self.rr_round) + 'done')



    def startGossip(self, gossip_protocol):
        if gossip_protocol == Constants.RANDOM_GOSSIP:
            self.initiateRandomGossip()

        elif gossip_protocol == Constants.RR_GOSSIP:
            self.initiateRRGossip()

        elif gossip_protocol == Constants.BRR_GOSSIP:
            self.initiateBinaryRRGossip()

        elif gossip_protocol == Constants.SCRR_GOSSIP:
            self.initiateSCRRGossip()

    def receiveGossip(self, digestList, clientIp):
        
        #TODO: add application version in later stage as well for comparison
        print('gossip received from--\n' + clientIp)
        # print('my digest', self.gDigestList)
        if self.gossip_protocol == Constants.SCRR_GOSSIP:
            indexOfClient = self.rr_list.index(clientIp)
            lastReceivedIp = self.rr_list[(indexOfClient + 1)%len(self.rr_list)]
            print("----->", lastReceivedIp)
            if lastReceivedIp != self.ip:
                if(lastReceivedIp != self.lastReceived['ip']) or \
                    (getDiffInSeconds(self.lastReceived['timestamp']) > Constants.WAIT_SECONDS_FAIL):
                    self.fault_vector[lastReceivedIp] = 1
                    monitor_client.updateSuspectMatrix(self.ip, self.fault_vector, self.getGeneration(lastReceivedIp))
        
            self.lastReceived['ip'] = clientIp
            self.lastReceived['timestamp'] = getTimeStamp()

        currenttList = copy.deepcopy(self.gDigestList)
        for ip, digest in digestList.items():
            if ip == self.ip:
                continue

            
            if ip in self.gDigestList:
                # print('if')
                if self.gDigestList[ip][1] < digest[1]:
                    currenttList[ip] = digest
                    try:
                        self.endpoint_state_map[ip]['appState']['App_version'] = digest[0]
                        self.endpoint_state_map[ip]['heartBeat']['generation'] = digest[1]
                        self.endpoint_state_map[ip]['heartBeat']['heartBeatValue'] = digest[2]
                    except Exception as e:
                        print('passed the exception')
                        pass            
                elif self.gDigestList[ip][2] < digest[2] and self.gDigestList[ip][1] == digest[1]:
                    currenttList[ip][2] = digest[2]
                    try:
                        self.endpoint_state_map[ip]['heartBeat']['heartBeatValue'] = digest[2]
                    except Exception as e:
                        print('passed the exception')
                        pass            
                
                    if self.gossip_version == Constants.ROUND_ROBIN:
                        self.updateAliveStatus(ip, clientIp)

            else:
                currenttList[ip] = digest
                   
            

        self.gDigestList = copy.deepcopy(currenttList)
        # updating timestamp for clientIp
        if clientIp in self.endpoint_state_map:
            self.updateAliveStatus(clientIp, clientIp)
