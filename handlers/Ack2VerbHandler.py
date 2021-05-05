"""
Author: Shreyas M
"""

import utilities.Constants as Constants

class Ack2VerbHandler(object):

    def __init__(self, arg):
        self.node = arg

    def updateEpStateMap(self, deltaEpStateMap, clientIp):
        """
        Authors: Shreyas M
        :param deltaEpStateMap:     Provides the endpoint state map for nodes that I don't have
        :param clientIp:    IP of sender node

        Updates values for meta-app state in endpoint state map and gossip digest list. No action required for the self node.
        """

        for ip, epState in deltaEpStateMap.items():
            #update by comparing which has the latest heartbeat
            if ip == self.node.ip:
                continue
            if ip in self.node.endpoint_state_map:
                if deltaEpStateMap[ip]["heartBeat"]["heartBeatValue"] > self.node.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"]: 
                    self.node.endpoint_state_map[ip] = deltaEpStateMap[ip]
                    #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                    self.node.gDigestList[ip] = [self.node.endpoint_state_map[ip]['appState']['App_version'], self.node.endpoint_state_map[ip]['heartBeat']['generation'], self.node.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
                    if self.node.gossip_version == Constants.ROUND_ROBIN:
                        self.node.updateAliveStatus(ip, clientIp)
            else:
                #since i don't know this ip, put entire epState for this ip
                self.node.endpoint_state_map[ip] = deltaEpStateMap[ip]
                #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                self.node.gDigestList[ip] = [self.node.endpoint_state_map[ip]['appState']['App_version'], self.node.endpoint_state_map[ip]['heartBeat']['generation'], self.node.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
            
