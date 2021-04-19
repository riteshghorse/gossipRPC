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


monitor_client = xmlrpc.client.ServerProxy(
    "http://" + Constants.MONITOR_ADDRESS + "/RPC2"
)


class Node(object):
    def __init__(self, host, port, id,*args,**kwargs):
        self.ip = str(host) + ":" + str(port)

        self.heart_beat_state = {
            "heartBeatValue": kwargs.get("heart_beat_state").get("heart_beat_value", None) if  kwargs.get("heart_beat_state", None) else Constants.INITIAL_HEARTBEAT,
            "generation": kwargs.get("heart_beat_state").get("generation", None) if  kwargs.get("heart_beat_state", None) else getCurrentGeneration(),
        }
        self.app_state = {
            "IP_Port": str(host) + ":" + str(port),
            "app_version": kwargs.get("app_state").get("app_version", None) if  kwargs.get("app_state", None) else Constants.APP_VERSION_DEFAULT,
            "app_status": kwargs.get("app_state").get("app_status", None) if  kwargs.get("app_state", None) else Constants.STATUS_NORMAL,
        }
        self.endpoint_state_map = {
            self.app_state["IP_Port"]: {
                "heartBeat": self.heart_beat_state,
                "appState": self.app_state,
                "last_updated_time": kwargs.get("endpoint_state").get("last_updated_time", None) if  kwargs.get("endpoint_state", None) else getTimeStamp(),
            }
        }
        self.gDigestList = {
            self.app_state["IP_Port"]: [
                self.app_state["app_version"],
                self.heart_beat_state["generation"],
                self.heart_beat_state["heartBeatValue"],
            ]
        }
        # {IP_Port:{'heartBeat':[version, generation], 'appState':[], 'last_msg_received': time}}
        # print(self.gDigestList)

        self.fault_vector = {self.ip: 0}
        self.live_nodes = list(self.ip)
        self.dead_nodes = list()
        self.handshake_nodes = list()
        self.message_count = 0
        self.rr_index = 0
        self.rr_list = None
        self.gossip_version = 0

    def updateHearbeat(self):
        self.heart_beat_state["heartBeatValue"] += 1
        self.endpoint_state_map[self.ip]["heartBeat"] = self.heart_beat_state
        self.gDigestList[self.ip][2] = self.heart_beat_state["heartBeatValue"]

    def sendSYN(self, sendTo):
        """
        sends SYN. Starts gossiping

        Note: If only one node is present in gDigestList
        """
        self.message_count += 1
        synDigest = SynGossipDigest(Constants.DEFAULT_CLUSTER, self.gDigestList)
        try:
            client = xmlrpc.client.ServerProxy("http://" + sendTo + "/RPC2")
            client.acceptSyn(synDigest, self.ip)
            print("SYN sent")
        except Exception as e:
            pass

        # sendAck2()

    def acceptSyn(self, synDigest, clientIp):
        self.message_count += 1
        variable = SynVerbHandler(self)
        deltaGDigest, deltaEpStateMap = variable.handleSync(synDigest)
        print("\nSyn handler completed")
        # print('DIgest contains: ', (deltaGDigest, self.endpoint_state_map))
        try:
            client = xmlrpc.client.ServerProxy("http://" + clientIp + "/RPC2")
            client.acceptAck(deltaGDigest, deltaEpStateMap, self.app_state["IP_Port"])
            print("\nACK sent")
        except Exception as e:
            pass
        # TODO: timer for ack expiry

    def updateAliveStatus(self, ip):
        # print('before\n', self.endpoint_state_map[ip]['last_updated_time'])
        self.endpoint_state_map[ip]["last_updated_time"] = getTimeStamp()
        # print('after \n', self.endpoint_state_map[ip]['last_updated_time'])
        # if ip in self.fault_vector and self.fault_vector[ip] == 1:
        if ip in self.fault_vector and self.fault_vector[ip] == 1:
            self.fault_vector[ip] = 0

            print("++++++++++++++", ip)
            monitor_client.updateSuspectMatrix(
                self.ip, self.fault_vector, self.getGeneration()
            )

    def acceptAck(self, deltaGDigest, deltaEpStateMap, clientIp):
        print("\nin accept ack")
        self.message_count += 1
        epStateMap = {}
        # print((deltaGDigest, deltaEpStateMap, clientIp))

        # retrieve meta-app states of requested IPs
        for ip in deltaGDigest:
            if ip in self.endpoint_state_map:
                epStateMap[ip] = self.endpoint_state_map[ip]

        # update my own meta-apps in endpoint

        for ip, epState in deltaEpStateMap.items():
            # update by comparing which has the latest heartbeat
            if ip in self.endpoint_state_map:
                if (
                    deltaEpStateMap[ip]["heartBeat"]["heartBeatValue"]
                    > self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"]
                ):
                    self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                    # gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                    self.gDigestList[ip] = [
                        self.endpoint_state_map[ip]["appState"]["app_version"],
                        self.endpoint_state_map[ip]["heartBeat"]["generation"],
                        self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"],
                    ]
                    if self.gossip_version == Constants.ROUND_ROBIN:
                        # self.endpoint_state_map[ip]['last_updated_time'] = getTimeStamp()
                        self.updateAliveStatus(ip)
            else:
                # since i don't know this ip, put entire epState for this ip
                self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                # gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                self.gDigestList[ip] = [
                    self.endpoint_state_map[ip]["appState"]["app_version"],
                    self.endpoint_state_map[ip]["heartBeat"]["generation"],
                    self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"],
                ]

        # print('updated epstate')
        # updating timestamp for clientIp
        if clientIp in self.endpoint_state_map:
            # self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()
            self.updateAliveStatus(clientIp)

        print("\nACK handled... sending ack2")

        if not self.isInHandshake(clientIp):
            self.handshake_nodes.append(clientIp)

        if not self.isInLivenodes(clientIp):
            self.live_nodes = list(self.endpoint_state_map.keys())

        try:
            client = xmlrpc.client.ServerProxy("http://" + clientIp + "/RPC2")
            client.acceptAck2(epStateMap, self.app_state["IP_Port"])
            print("\nACK2 sent")
        except Exception as e:
            pass

    def acceptAck2(self, deltaEpStateMap, clientIp):
        print("\n in acceptAck 2")
        self.message_count += 1

        for ip, epState in deltaEpStateMap.items():
            # update by comparing which has the latest heartbeat
            if ip == self.ip:
                continue
            if ip in self.endpoint_state_map:
                if (
                    deltaEpStateMap[ip]["heartBeat"]["heartBeatValue"]
                    > self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"]
                ):
                    self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                    # gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                    self.gDigestList[ip] = [
                        self.endpoint_state_map[ip]["appState"]["app_version"],
                        self.endpoint_state_map[ip]["heartBeat"]["generation"],
                        self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"],
                    ]
                    if self.gossip_version == Constants.ROUND_ROBIN:
                        self.updateAliveStatus(ip)
            else:
                # since i don't know this ip, put entire epState for this ip
                self.endpoint_state_map[ip] = deltaEpStateMap[ip]
                # gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                self.gDigestList[ip] = [
                    self.endpoint_state_map[ip]["appState"]["app_version"],
                    self.endpoint_state_map[ip]["heartBeat"]["generation"],
                    self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"],
                ]

        if not self.isInHandshake(clientIp):
            self.handshake_nodes.append(clientIp)

        if not self.isInLivenodes(clientIp):
            self.live_nodes = list(self.endpoint_state_map.keys())

        # updating timestamp of clientIp
        # self.endpoint_state_map[clientIp]['last_updated_time'] = getTimeStamp()

        self.updateAliveStatus(clientIp)
        print("\n ACK2 processed... complete handshake")

    def getGeneration(self, clientIp):
        if clientIp in self.endpoint_state_map:
            self.endpoint_state_map[clientIp]["heartBeat"]["generation"]
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
                    client = xmlrpc.client.ServerProxy("http://" + ip + "/RPC2")
                    client.receiveGossip(self.gDigestList, self.ip)
                except Exception as e:
                    pass
            else:
                print("--------------------> sending syn" + ip)
                self.sendSYN(ip)

    def initiateRRGossip(self):
        if self.rr_index == 0:
            self.rr_list = copy.deepcopy(self.gDigestList)
            self.rr_list.pop(self.ip, None)

        print("-------------")
        print(self.rr_list, self.fault_vector)
        print(self.endpoint_state_map)
        print("-------------")

        from gossip_server import scheduler, scheduleGossip

        print("In round: " + str(self.rr_index))
        keyList = list(self.rr_list.keys() - self.ip)

        self.message_count += 1
        ip = keyList[self.rr_index]
        if self.isInHandshake(ip):
            try:
                client = xmlrpc.client.ServerProxy("http://" + ip + "/RPC2")
                client.receiveGossip(self.gDigestList, self.ip)
            except Exception as e:
                pass
        else:
            print("--------------------> sending syn" + ip)
            self.sendSYN(ip)
        self.rr_index = (self.rr_index + 1) % len(self.rr_list)
        print("round robin " + str(self.rr_index) + "done")

    def startGossip(self, gossip_protocol):
        if gossip_protocol == Constants.RANDOM_GOSSIP:
            self.initiateRandomGossip()

        elif gossip_protocol == Constants.RR_GOSSIP:
            self.initiateRRGossip()

    def receiveGossip(self, digestList, clientIp):

        # TODO: add application version in later stage as well for comparison
        print("gossip received from--\n" + clientIp, digestList)
        # print('my digest', self.gDigestList)
        currenttList = copy.deepcopy(self.gDigestList)
        for ip, digest in digestList.items():
            if ip == self.ip:
                continue

            if ip in self.gDigestList:
                # print('if')
                if self.gDigestList[ip][1] < digest[1]:
                    currenttList[ip] = digest
                    self.endpoint_state_map[ip]["appState"]["app_version"] = digest[0]
                    self.endpoint_state_map[ip]["heartBeat"]["generation"] = digest[1]
                    self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"] = digest[
                        2
                    ]
                elif (
                    self.gDigestList[ip][2] < digest[2]
                    and self.gDigestList[ip][1] == digest[1]
                ):
                    self.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"] = digest[
                        2
                    ]
                    currenttList[ip][2] = digest[2]
                    if self.gossip_version == Constants.ROUND_ROBIN:
                        self.updateAliveStatus(ip)
            else:
                currenttList[ip] = digest

        self.gDigestList = currenttList
        # updating timestamp for clientIp
        if clientIp in self.endpoint_state_map:
            self.updateAliveStatus(clientIp)
