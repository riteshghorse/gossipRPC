from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
from collections import defaultdict

# Required Data Structures

endpoint_state_map = defaultdict(defaultdict())  #{IP_Port:{'heartBeat':[version, generation], 'appState':[], 'last_msg_received': time}}
heart_beat_state = defaultdict() #{"heartBeatValue": , "generation": } 
app_state = defaultdict() # {"IP_Port": , "App_version": , "App status": }
# suspect_matrix = list(list)
fault_vector = list()   
live_nodes = set()
dead_nodes = set()


# gDigest = {IP_port : [Application_version, generation, heartbeat_value]} 





class AckGossipDigest:
    def __init__(self, gDigestList, epStateMap):
        self._gDigestList = gDigestList
        self._epStateMap = epStateMap

    def getDigestList(self):
        return self._gDigestList

    def getEpStateMap(self):
        return self._epStateMap



class AckVerbHandler:
    def handleAck(self, ackDigestMessage):
        gDigestList = ackDigestMessage.getDigestList()
        epStateMap = ackDigestMessage.getEpStateMap()

        deltaEpStateMap = defaultdict()

        for gDigest in gDigestList:
            IP_port = list(gDigest.keys())[0]
            deltaEpStateMap[IP_port] = endpoint_state_map[IP_port]

        for k,v in epStateMap:
            if epStateMap[k]["heartBeat"][0] > endpoint_state_map[k]["heartBeat"][0]: 
                endpoint_state_map[k] = v

        # send ack2 gossip digest
          

class Ack2GossipDigest:
    def __init__(self, epStateMap):
        self._epStateMap = epStateMap

    def getEpStateMap(self):
        return self._epStateMap


class Ack2VerbHandler:
    def handleAck2(self, ack2DigestMessage):
        epStateMap = ack2DigestMessage.getEpStateMap()
        

        for inp, epState in epStateMap.items():
       
            if inp in endpoint_state_map.keys():
                remote_generation = gDigestList[IP_port][1]
                remote_heartbeat = gDigestList[IP_port][2]

                if (heart_beat_state["generation"] < remote_generation):
                    endpoint_state_map[inp] = epState

                elif heart_beat_state["generation"] == remote_generation:
                    if heart_beat_state["heartBeatValue"] < remote_heartbeat:
                        endpoint_state_map[inp] = epState

            else:
                endpoint_state_map[inp] = epState



def markDead(ip):
    """
    automatically triggered after Tclean_up
    """
    global live_nodes
    global dead_nodes
    global fault_vector

    live_nodes.remove(ip)
    dead_nodes.insert(ip)
    with xmlrpc.client.ServerProxy("http://localhost:8000/") as proxy:
        index = proxy.getMapping()[ip]

        fault_vector[index] = 1
        updateSuspectMatrix(ip, fault_vector)
        

    

server = SimpleXMLRPCServer(("localhost", 8001))
print("Listening on port 8001...")
server.register_function(is_even, "is_even")
# server.serve_forever()

with xmlrpc.client.ServerProxy("http://localhost:8002/") as proxy:
    print("3 is odd: %s" % str(proxy.is_odd(3)))
    print("100 is odd: %s" % str(proxy.is_odd(100)))

server.serve_forever()