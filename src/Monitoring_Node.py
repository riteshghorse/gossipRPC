from xmlrpc.server import SimpleXMLRPCServer
from collections import defaultdict


node_index = 0
IP_to_Node_Index = {}
Index_to_IP = {}
suspect_matrix = [[]]
global_fault_vector = []

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

server.serve_forever()