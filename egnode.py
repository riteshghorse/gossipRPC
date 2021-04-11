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



monitor_client =  xmlrpc.client.ServerProxy('http://' + Constants.MONITOR_ADDRESS + '/RPC2')

class Node(object):

    def __init__(self, host, port, id):
        self.ip = str(host) + ':' + str(port)

        self.heart_beat_state = {"heartBeatValue": Constants.INITIAL_HEARTBEAT, "generation": getCurrentGeneration()} 
        self.app_state = {"IP_Port": str(host)+':'+str(port) , "App_version": Constants.APP_VERSION_DEFAULT, "App_status": Constants.STATUS_NORMAL}
        self.endpoint_state_map = {self.app_state["IP_Port"]: {'heartBeat': self.heart_beat_state, 'appState':self.app_state, 'last_updated_time': 0}}
        self.gDigestList = {self.app_state['IP_Port'] : [self.app_state['App_version'], self.heart_beat_state['generation'], self.heart_beat_state['heartBeatValue']]} 
        #{IP_Port:{'heartBeat':[version, generation], 'appState':[], 'last_msg_received': time}}
        # print(self.gDigestList)
        
        self.fault_vector = {self.ip:0}  
        self.live_nodes = list()
        self.dead_nodes = list()
        self.handshake_nodes = list()
        self.message_count = 0
        self.rr_index = 0
        # self.rr_list = list(list)

    def updateHearbeat(self):
        self.heart_beat_state["heartBeatValue"] += 1
        
        self.endpoint_state_map[self.ip]['heartBeat'] = self.heart_beat_state
        self.gDigestList[self.ip][2] = self.heart_beat_state['heartBeatValue'] 
        # if self.ip == 'localhost:5002':
        #     print('-----\n', self.heart_beat_state)
        #     print(self.endpoint_state_map[self.ip]['heartBeat'])
        #     print(self.gDigestList[self.ip][2])
        #     print(self.gDigestList)
        # print(self.heart_beat_state["heartBeatValue"])

    def sendSYN(self, sendTo):
        """
        sends SYN. Starts gossiping

        Note: If only one node is present in gDigestList
        """
        self.message_count += 1
        synDigest = SynGossipDigest(Constants.DEFAULT_CLUSTER, self.gDigestList)
        # print("\nin send")
        # if len(self.gDigestList) == 1:
        #     sendTo = str(ConfigurationManager.get_configuration().get_seed_host()) + ':' + str(ConfigurationManager.get_configuration().get_seed_port())
        # else:
        #     sendTo = 'localhost:5001'   #TODO: change it to random

        print(self.ip)

        # print('--------'+sendTo)
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
        
        # self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()
        print(clientIp)
        # print()
        # self.endpoint_state_map[]
        print('\nSyn handler completed')
        # print('DIgest contains: ', (deltaGDigest, self.endpoint_state_map))
        try:
            client =  xmlrpc.client.ServerProxy('http://' + clientIp + '/RPC2')
            client.acceptAck(deltaGDigest, deltaEpStateMap, self.app_state["IP_Port"])
            print('\nACK sent')
        except Exception as e:
            pass
        #TODO: timer for ack expiry

    def acceptAck(self, deltaGDigest, deltaEpStateMap, clientIp):
        print('\nin accept ack')
        self.message_count += 1
        epStateMap = {}
        # print((deltaGDigest, deltaEpStateMap, clientIp))

        # retrieve meta-app states of requested IPs
        for ip in deltaGDigest:
            if ip in self.endpoint_state_map:
                epStateMap[ip] = self.endpoint_state_map[ip]
                # print('////////////////////////////')

        # print('+++++++++++++++++++delta map',deltaEpStateMap)
        #update my own meta-apps in endpoint
        for ip, epState in deltaEpStateMap.items():
            # print(ip, epState )
            #update by comparing which has the latest heartbeat
            if ip in self.endpoint_state_map:
                if deltaEpStateMap[ip]["heartBeat"]["heartBeatValue"] > self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"]: 
                    self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                    #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                    self.gDigestList[ip] = [self.endpoint_state_map[ip]['appState']['App_version'], self.endpoint_state_map[ip]['heartBeat']['generation'], self.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
            else:
                #since i don't know this ip, put entire epState for this ip
                self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                self.gDigestList[ip] = [self.endpoint_state_map[ip]['appState']['App_version'], self.endpoint_state_map[ip]['heartBeat']['generation'], self.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
        print('updated epstate')
        # updating timestamp for clientIp
        if clientIp in self.endpoint_state_map:
            self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()
            if clientIp in self.fault_vector:
                self.fault_vector[clientIp] = 0
                monitor_client.updateSuspectMatrix(self.ip, self.fault_vector)

        print("\nACK handled... sending ack2")
        
        if not self.isInHandshake(clientIp):
            self.handshake_nodes.append(clientIp)

        if not self.isInLivenodes(clientIp):
            self.live_nodes.append(self.endpoint_state_map.keys() - self.ip)
        
        try:
            client =  xmlrpc.client.ServerProxy('http://' + clientIp + '/RPC2')
            client.acceptAck2(epStateMap, self.app_state["IP_Port"])
            print("\nACK2 sent")
        except Exception as e:
            pass
        # print((self.handshake_nodes, self.live_nodes))
        # print(self.endpoint_state_map)




    def acceptAck2(self, deltaEpStateMap, clientIp):
        print('\n in acceptAck 2')
        self.message_count += 1
        for ip, epState in deltaEpStateMap.items():
            #update by comparing which has the latest heartbeat
            if ip in self.endpoint_state_map:
                if deltaEpStateMap[ip]["heartBeat"]["heartBeatValue"] > self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"]: 
                    self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                    #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                    self.gDigestList[ip] = [self.endpoint_state_map[ip]['appState']['App_version'], self.endpoint_state_map[ip]['heartBeat']['generation'], self.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
            else:
                #since i don't know this ip, put entire epState for this ip
                self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                self.gDigestList[ip] = [self.endpoint_state_map[ip]['appState']['App_version'], self.endpoint_state_map[ip]['heartBeat']['generation'], self.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
        
        
        if not self.isInHandshake(clientIp):
            self.handshake_nodes.append(clientIp)
            
        if not self.isInLivenodes(clientIp):
            self.live_nodes.append(self.endpoint_state_map.keys() - self.ip)

        # updating timestamp of clientIp
        self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()
        
        if clientIp in self.fault_vector:
            self.fault_vector[clientIp] = 0
            monitor_client.updateSuspectMatrix(self.ip, self.fault_vector)
        print('\n ACK2 processed... complete handshake')
        print(self.handshake_nodes, self.live_nodes)
        # print((self.handshake_nodes, self.live_nodes))
        # print(self.endpoint_state_map)


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
    
        # print(self.gDigestList)
        digestList = copy.deepcopy(self.gDigestList)

        digestList.pop(self.ip, None)
        # self.gDigestList['localhost:5003'] = [1,2,3]
        # print(self.gDigestList)
        # print(digestList, self.gDigestList)
        from gossip_server import scheduler, scheduleGossip

        # if(len(digestList) <= 3):
        #     for ip, digest in digestList.items():
        #         self.message_count += 1
        #         # print('in start+-+-+-+-+-+-+-+-+-+-+++-+--++-',self.handshake_nodes)
        #         if ip == self.ip:
        #             continue
                
        #         if self.isInHandshake(ip):
        #             try:
        #                 client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
        #                 client.receiveGossip(self.gDigestList, self.ip)
        #             except Exception as e:
        #                 pass
        #         else:
        #             print('--------------------> sending syn'+ip)
        #             # client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
        #             # client.sendSYN(ip)
        #             self.sendSYN(ip)
        #             # print('doing it')
        # else:
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
                # client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                # client.sendSYN(ip)
                self.sendSYN(ip)
                # print('doing it')


    # def createRRList(self, digestList):
        

    def initiateRRGossip(self):

        
        digestList = copy.deepcopy(self.gDigestList)
        digestList.pop(self.ip, None)
        # if self.rr_index == 0:
        #     self.createRRList()

        from gossip_server import scheduler, scheduleGossip

        if(len(digestList) <= 3):
            for ip, digest in digestList.items():
                self.message_count += 1
                
                if ip == self.ip:
                    continue
                
                if self.isInHandshake(ip):
                    try:
                        client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                        client.receiveGossip(self.gDigestList, self.ip)
                    except Exception as e:
                        pass
                else:
                    print('--------------------> sending syn'+ip)
                    self.sendSYN(ip)
        else:
            






            keyList = list(digestList.keys() - self.ip)
            random_numbers = sample(range(0, len(keyList)), 3)
            # print('-------------------------------------------------')
            self.message_count += 3
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


    def startGossip(self, gossip_protocol):
        if gossip_protocol == Constants.RANDOM_GOSSIP:
            self.initiateRandomGossip()

        elif gossip_protocol == Constants.RR_GOSSIP:
            self.initiateRRGossip()

    def receiveGossip(self, digestList, clientIp):
        
        #TODO: add application version in later stage as well for comparison
        print('gossip received from--\n' + clientIp, digestList)
        print('my digest', self.gDigestList)
        currenttList = copy.deepcopy(self.gDigestList)
        for ip, digest in digestList.items():
            if ip == self.ip:
                continue
        #     print('--------------------')
        #     if ip in self.gDigestList:
        #         print('ingdigest')
                
        #     if ip in self.endpoint_state_map:
        #         print('epmap')
        #     print('---------------------')
            if ip in self.gDigestList:
                # print('if')
                if self.gDigestList[ip][1] < digest[1]:
                    currenttList[ip] = digest
                    self.endpoint_state_map[ip]['appState']['App_version'] = digest[0]
                    self.endpoint_state_map[ip]['heartBeat']['generation'] = digest[1]
                    self.endpoint_state_map[ip]['heartBeat']['heartBeatValue'] = digest[2]
                elif self.gDigestList[ip][2] < digest[2] and self.gDigestList[ip][1] == digest[1]:
                    self.endpoint_state_map[ip]['heartBeat']['heartBeatValue'] = digest[2]
                    currenttList[ip][2] = digest[2]
            else:
                # print('else')
        #         print('------>'+clientIp)
                # print(self.gDigestList, (ip, digest))
                # self.gDigestList.update({ip:digest})
                # self.gDigestList[ip] = []
                currenttList[ip] = digest
                # print("Assignment complete -",  )
                # argdict = {ip:digest}
                # self.gDigestList = {**self.gDigestList}
        self.gDigestList = currenttList
        print('------------------------------')
        print(self.ip, self.gDigestList)
        print('------------------------------')
        # updating timestamp for clientIp
        if clientIp in self.endpoint_state_map:
            self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()
            if clientIp in self.fault_vector:
                self.fault_vector[clientIp] = 0
                monitor_client.updateSuspectMatrix(self.ip, self.fault_vector)
        # print('reassigned************************')
