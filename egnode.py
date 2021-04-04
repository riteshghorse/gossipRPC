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




class Node(object):

    def __init__(self, host, port, id):
        self.ip = str(host) + ':' + str(port)

        self.heart_beat_state = {"heartBeatValue": Constants.INITIAL_HEARTBEAT, "generation": getCurrentGeneration()} 
        self.app_state = {"IP_Port": str(host)+':'+str(port) , "App_version": Constants.APP_VERSION_DEFAULT, "App status": Constants.STATUS_NORMAL}
        self.endpoint_state_map = {self.app_state["IP_Port"]: {'heartBeat': self.heart_beat_state, 'appState':self.app_state, 'last_updated_time': 0}}
        self.gDigestList = {self.app_state['IP_Port'] : [self.app_state['App_version'], self.heart_beat_state['generation'], self.heart_beat_state['heartBeatValue']]} 
        #{IP_Port:{'heartBeat':[version, generation], 'appState':[], 'last_msg_received': time}}
        print(self.gDigestList)
        
        self.fault_vector = list()   
        self.live_nodes = list()
        self.dead_nodes = list()
        self.handshake_nodes = list()


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
        synDigest = SynGossipDigest(Constants.DEFAULT_CLUSTER, self.gDigestList)
        print("\nin send")
        # if len(self.gDigestList) == 1:
        #     sendTo = str(ConfigurationManager.get_configuration().get_seed_host()) + ':' + str(ConfigurationManager.get_configuration().get_seed_port())
        # else:
        #     sendTo = 'localhost:5001'   #TODO: change it to random

        print(self.ip)

        print('--------'+sendTo)
        client =  xmlrpc.client.ServerProxy('http://' + sendTo + '/RPC2')
        client.acceptSyn(synDigest, self.ip)
        print("SYN sent")
        
        # sendAck2()


    def acceptSyn(self,synDigest, clientIp):
        variable = SynVerbHandler(self)
        deltaGDigest, deltaEpStateMap = variable.handleSync(synDigest)
        
        # self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()
        print(clientIp)
        # print()
        # self.endpoint_state_map[]
        print('\nSyn handler completed')
        # print('DIgest contains: ', (deltaGDigest, self.endpoint_state_map))
        client =  xmlrpc.client.ServerProxy('http://' + clientIp + '/RPC2')
        client.acceptAck(deltaGDigest, deltaEpStateMap, self.app_state["IP_Port"])
        print('\nACK sent')
        #TODO: timer for ack expiry

    def acceptAck(self, deltaGDigest, deltaEpStateMap, clientIp):
        print('\nin accept ack')
        epStateMap = {}
        # print((deltaGDigest, deltaEpStateMap, clientIp))

        # retrieve meta-app states of requested IPs
        for ip in deltaGDigest:
            if ip in self.endpoint_state_map:
                epStateMap[ip] = self.endpoint_state_map[ip]
                print('////////////////////////////')

        print('+++++++++++++++++++delta map',deltaEpStateMap)
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
        # updating timestamp for clientIp
        if clientIp in self.endpoint_state_map:
            self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()

        print("\nACK handled... sending ack2")
        
        if not self.isInHandshake(clientIp):
            self.handshake_nodes.append(clientIp)
        if not self.isInLivenodes(clientIp):
            self.live_nodes.append(self.endpoint_state_map.keys() - self.ip)
        
        client =  xmlrpc.client.ServerProxy('http://' + clientIp + '/RPC2')
        client.acceptAck2(epStateMap, self.app_state["IP_Port"])
        print("\nACK2 sent")
        # print((self.handshake_nodes, self.live_nodes))
        # print(self.endpoint_state_map)




    def acceptAck2(self, deltaEpStateMap, clientIp):
        print('\n in acceptAck 2')

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

    def startGossip(self, gossip_protocol):
        if gossip_protocol == Constants.RANDOM_GOSSIP:
            # print(self.gDigestList)
            digestList = copy.deepcopy(self.gDigestList)

            digestList.pop(self.ip, None)
            # self.gDigestList['localhost:5003'] = [1,2,3]
            # print(self.gDigestList)
            # print(digestList, self.gDigestList)
            from gossip_server import scheduler, scheduleGossip
            if(len(digestList) <= 3):
                for ip, digest in digestList.items():
                    print('in start+-+-+-+-+-+-+-+-+-+-+++-+--++-',self.handshake_nodes)
                    if ip == self.ip:
                        continue
                    
                    if self.isInHandshake(ip):
                        client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                        client.receiveGossip(self.gDigestList, self.ip)
                    else:
                        print('--------------------> sending syn'+ip)
                        # client =  xmlrpc.client.ServerProxy('http://' + ip + '/RPC2')
                        # client.sendSYN(ip)
                        self.sendSYN(ip)
                        # print('doing it')
                

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
                print('if')
                if self.gDigestList[ip][1] < digest[1]:
                    currenttList[ip] = digest
                    self.endpoint_state_map[ip]['appState']['App_version'] = digest[0]
                    self.endpoint_state_map[ip]['heartBeat']['generation'] = digest[1]
                    self.endpoint_state_map[ip]['heartBeat']['heartBeatValue'] = digest[2]
                elif self.gDigestList[ip][2] < digest[2] and self.gDigestList[ip][1] == digest[1]:
                    self.endpoint_state_map[ip]['heartBeat']['heartBeatValue'] = digest[2]
                    currenttList[ip][2] = digest[2]
            else:
                print('else')
        #         print('------>'+clientIp)
                print(self.gDigestList, (ip, digest))
                # self.gDigestList.update({ip:digest})
                # self.gDigestList[ip] = []
                currenttList[ip] = digest
                print("Assignment complete -",  )
                # argdict = {ip:digest}
                # self.gDigestList = {**self.gDigestList}
        self.gDigestList = currenttList
        print('reassigned************************')

    def get_id_of_node(self, calling_id):
        print("Calling {} from {}.".format(self.id, calling_id))
        return self.id


    def contact_node(self, host, port):
        client =  xmlrpc.client.ServerProxy('http://' + host + ":" + str(port) + '/RPC2')
        contact_node_id = client.get_id_of_node(self.id)
        print("Contact node with id: {}".format(contact_node_id))