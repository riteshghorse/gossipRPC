from xmlrpc.server import SimpleXMLRPCServer
from collections import defaultdict


node_index = 0
IP_to_Node_Index = {}
Index_to_IP = {}
suspect_matrix = [[]]
global_fault_vector = []
global_state_map = defaultdict(defaultdict())

def setMapping(ip):
    
    global node_index
    global global_fault_vector
    global Index_to_IP
    global IP_to_Node_Index
    global suspect_matrix

    if ip in IP_to_Node_Index:
        return
    global_fault_vector.extend([0])
    IP_to_Node_Index[ip] = node_index
    Index_to_IP[node_index] = ip
    for row in suspect_matrix:
        row.extend([0])

    if(len(suspect_matrix[0]) > 1):
        suspect_matrix.append([0 for i in range(len(suspect_matrix[0]))])
    print(suspect_matrix)
    # print(getMapping())
    print('\n') 
    node_index += 1

def getMapping():
    return IP_to_Node_Index


def updateSuspectMatrix(ip, fault_vector):
    global suspect_matrix
    
    index = getMapping()[ip]
    suspect_matrix[index] = fault_vector
    doConsensus()
    print(global_fault_vector)


def sendEpStateMap(ip, epStateMap):
    reveiveStateMap(ip, epStateMap)
    

def receiveStateMap(ip, epStateMap):
    global global_state_map
    global_state_map[ip] = epStateMap


def doConsensus():
    global global_fault_vector

    for j in range(len(suspect_matrix[0])):
        state = 1
        for i in range(len(suspect_matrix)):
            if i != j:
                state &= suspect_matrix[i][j]
        if(state == 1):
            print("Node %s is failed" % (Index_to_IP[j]))                
        else:
            print("Node %s is alive" % (Index_to_IP[j]))                
        global_fault_vector[j] = state

server = SimpleXMLRPCServer(("localhost", 8000), allow_none = True)
print("Listening on port 8000...")
server.register_function(setMapping, "setMapping")
server.register_function(getMapping, "getMapping")
server.register_function(updateSuspectMatrix, "updateSuspectMatrix")



if __name__ == "__main__":

    # configuration_file, bootstrap_server, server_id, no_hash = get_arguments()
    
    start_gossip_node(node)
    
    # register this node to monitoring node
    proxy.setMapping(str(server_id)+str(port))

    flag = 0
    scheduler.enter(1, 1, stabilize_call, (node,))
    stabilization_thread = threading.Thread(target=scheduler.run, args=(True,))
    stabilization_thread.start()
    #update heartbeat every 1 sec
    # happens internally
    # node.updateHearbeat()
    # rt = RepeatedTimer(1, node.updateHearbeat())
    # threading.Timer(Constants.WAIT_SECONDS_HEARTBEAT, node.updateHearbeat()).start()
    while True:
        # time.sleep(5)
        # node.sendSYN()

        # while flag:

        # t = threading.Timer(Constants.WAIT_SECONDS_HEARTBEAT, node.updateHearbeat()).start()

        print("\n\nRunning with server id : " + str(server_id))
        console_input = input("1. \"stop\" to shutdown gossip node\n2. \"contact\" to contact one of the node\n"
                              "Enter your input:")
        
        if console_input.strip() == "stop":
            stop_gossip_node()
            break

        if console_input.strip() == "contact":
            flag = 1

server.serve_forever()