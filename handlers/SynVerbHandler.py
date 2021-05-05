"""
Author: Shreyas M
"""
from handlers.SynGossipDigest import *
from collections import defaultdict

class SynVerbHandler(object):

    def __init__(self, arg):
        self.node = arg

    def handleSync(self, synDigestMessage):
        """
        Authors: Shreyas M
        :param synDigestMessage:    Message digest shared during gossip or handshake.

        Extract the digest list from message digest and update my end point statemap accordingly.
        """
        gDigestList = SynGossipDigest.getGossipDigest(synDigestMessage)
        deltaGDigest = list()
        deltaEpStateMap = defaultdict()

        (deltaGDigest, deltaEpStateMap) = self.examine_gossip(gDigestList)

        #send it in Ack
        return (deltaGDigest, deltaEpStateMap)


    
    def examine_gossip(self,gDigestList):
        """
        Authors: Shreyas M
        :param gDigestList:    List of active nodes in cluster and meta state information

        Update endpoint state map based on the heard beat generation and heartbeat value.
        """
        deltaGDigest = list()
        deltaEpStateMap = {self.node.ip: self.node.endpoint_state_map[self.node.app_state['IP_Port']]}
        # print('gdigest', gDigestList)

        for inp, gDigest in gDigestList.items():
            if inp == self.node.ip:
                continue
            # print('in gossip ')
            IP_port = inp
       
            if IP_port in self.node.endpoint_state_map.keys():
                remote_generation = gDigestList[IP_port][1]
                remote_heartbeat = gDigestList[IP_port][2]

                if (self.node.heart_beat_state["generation"] < remote_generation):
                    deltaGDigest.append(IP_port)

                elif self.node.heart_beat_state["generation"] == remote_generation:
                    if self.node.heart_beat_state["heartBeatValue"] < remote_heartbeat:
                        deltaGDigest.append(IP_port)
                    
                    elif self.node.heart_beat_state["heartBeatValue"] > remote_heartbeat:
                        deltaEpStateMap[IP_port] = self.node.endpoint_state_map[IP_port]
                        # print('in examine', deltaEpStateMap)
            
            else:
                deltaGDigest.append(IP_port)
                

        return (deltaGDigest,deltaEpStateMap)

