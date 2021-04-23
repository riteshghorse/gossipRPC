import Constants

class AckVerbHandler(object):

    def __init__(self, arg):
        self.node = arg

    def setEpStateMap(self, deltaGDigest):
        epStateMap = {}
        for ip in deltaGDigest:
            if ip in self.node.endpoint_state_map:
                epStateMap[ip] = self.node.endpoint_state_map[ip]
        return epStateMap
                

    def updateEpStateMap(self, deltaEpStateMap, clientIp):
        for ip, epState in deltaEpStateMap.items():
            #update by comparing which has the latest heartbeat
            if ip in self.node.endpoint_state_map:
                if deltaEpStateMap[ip]["heartBeat"]["heartBeatValue"] > self.node.endpoint_state_map[ip]["heartBeat"]["heartBeatValue"]: 
                    self.node.endpoint_state_map[ip] = deltaEpStateMap[ip]
                    #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                    self.node.gDigestList[ip] = [self.node.endpoint_state_map[ip]['appState']['App_version'], self.node.endpoint_state_map[ip]['heartBeat']['generation'], self.node.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
                    if self.node.gossip_version == Constants.ROUND_ROBIN:
                        # self.endpoint_state_map[ip]['last_updated_time'] = getTimeStamp()
                        self.node.updateAliveStatus(ip, clientIp)
            else:
                #since i don't know this ip, put entire epState for this ip
                self.node.endpoint_state_map[ip] = deltaEpStateMap[ip]
                #gDIgest list will be forwarded in next rounds of gossip hence it has to be updated
                self.node.gDigestList[ip] = [self.node.endpoint_state_map[ip]['appState']['App_version'], self.node.endpoint_state_map[ip]['heartBeat']['generation'], self.node.endpoint_state_map[ip]['heartBeat']['heartBeatValue']]
        
