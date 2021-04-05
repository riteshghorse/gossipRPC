
class SynVerbHandler:

    def handleSync(self, synDigestMessage):
        gDigestList = synDigestMessage.getGossipDigest()
        deltaGDigest = list()
        deltaEpStateMap = defaultdict()

        (deltaGDigest, deltaEpStateMap) = examine_gossip(gDigestList)

        #send it in Ack
        return (deltaGDigest, deltaEpStateMap)


    
    def examine_gossip(self,gDigestList):

        deltaGDigest = list()
        deltaEpStateMap = defaultdict()

        for gDigest in gDigestList:
            IP_port = list(gDigest.keys())[0]
       
            if IP_port in endpoint_state_map.keys():
                remote_generation = gDigestList[IP_port][1]
                remote_heartbeat = gDigestList[IP_port][2]

                if (heart_beat_state["generation"] < remote_generation):
                    deltaGDigest.append(IP_Port)

                elif heart_beat_state["generation"] == remote_generation:
                    if heart_beat_state["heartBeatValue"] < remote_heartbeat:
                        deltaGDigest.append(IP_Port)
                    
                    elif heart_beat_state["heartBeatValue"] > remote_heartbeat:
                        deltaEpStateMap[IP_Port] = endpoint_state_map[IP_Port]
            
            else:
                deltaGDigest.append(IP_Port)

        return (deltaGDigest,deltaEpStateMap)

