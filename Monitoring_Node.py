# Author: Ritesh G, Shreyas M




from xmlrpc.server import SimpleXMLRPCServer
from collections import defaultdict
from gossip_server import get_arguments, start_gossip_node, stop_gossip_node
from gossip_rpc.config import Configuration
import os
import time
import copy
from utilities.utils import *
import utilities.Constants as Constants

class MonitoringNode:
    """
    Author: Ritesh G, Shreyas M
    Independent Node to passively receive information from 
    other nodes in cluster. 

    1. Keeps track of nodes joining the network.
    2. Shows the state of cluster.
    3. Implementation of Consensus Algorithm

    NOTE: This node is not a part of cluster and it doesn't participate 
          or provide information to any node in the cluster.
    """
    def __init__(self):
        # Author: Ritesh G
        self.node_index = 0                                 # order of node joining
        self.IP_to_Node_Index = {}          
        self.Index_to_IP = {}
        self.suspect_matrix = [[]]                          # matrix of fault vectors of every node.
        self.global_fault_vector = []                       # overall state of network. 1 is FAIL.
        self.global_state_map = defaultdict(defaultdict)    # State of cluster
        self.start_time = None               
        self.total_msg_count = 0
        self.consensusMap = defaultdict(defaultdict)
        self.ip_generation = defaultdict()                  # records node's generation at which failure occured.
        self.heartbeatTime = {}
        self.false_failure_count = 0

    def setheartbeatTime(self, ip):
        self.heartbeatTime[ip] = getTimeStamp()

    def setMapping(self,ip):
        """
        Author: Ritesh G
        :param ip: new IP joining the network

        Intializes Fault vector for this IP and updates global fault vector.
        """
        if ip in self.IP_to_Node_Index:
            self.suspect_matrix[self.IP_to_Node_Index[ip]] = list(self.global_fault_vector)
            return

        self.global_fault_vector.extend([0])
        self.IP_to_Node_Index[ip] = self.node_index
        self.Index_to_IP[self.node_index] = ip
        
        for row in self.suspect_matrix:
            row.extend([0])

        if(len(self.suspect_matrix[0]) > 1):
            self.suspect_matrix.append(list(self.global_fault_vector))

        self.node_index += 1

    def getMapping(self):
        """
        Author: Ritesh G

        Used in front-end of Flask.
        """
        return self.IP_to_Node_Index


    def updateSuspectMatrix(self, ip, fault_vector, generation):
        """
        Author: Ritesh G
        :param ip          : IP who is telling to update status for nodes is fault_vector
        :param fault_vector: new status of nodes according to IP
        "param generation  : used in false failure detection. 
        """
        try:
            if self.global_fault_vector[self.IP_to_Node_Index[ip]] == 1:
                self.global_fault_vector[self.IP_to_Node_Index[ip]] = 0
        except Exception as e:
            pass
        for k,v in fault_vector.items():
            if v==0:
                try:
                    if(self.IP_to_Node_Index[k] in self.ip_generation and generation == self.ip_generation[self.IP_to_Node_Index[k]]):
                        # if generation for a node which was previously detected FAIL is same as 
                        # current generation in alive state then it was a FALSE FAILURE DETECTION
                        print('False failure detection happened for ', k)        
                        self.false_failure_count += 1  
                except Exception as e:
                    pass
            
            self.suspect_matrix[self.IP_to_Node_Index[ip]][self.IP_to_Node_Index[k]] = v 
        self.doConsensus()


    def getFaultVector(self):
        """
        Author: Ritesh G

        Used in front-end of Flask.
        """
        return self.global_fault_vector

    def showAliveDeadNode(self):
        # Author: Ritesh G
        live_nodes = [self.Index_to_IP[ip] for ip,status in enumerate(self.global_fault_vector) if status!=1]
        dead_nodes = [self.Index_to_IP[ip] for ip,status in enumerate(self.global_fault_vector) if status==1]
        return {'live': live_nodes, 'dead': dead_nodes}

    def sendEpStateMap(self, ip, epStateMap, msg_count):
        # Author: Ritesh G
        self.receiveStateMap(ip, epStateMap, msg_count)
        

    def receiveStateMap(self, ip, epStateMap, msg_count):
        """
        Author: Ritesh G

        Receives information from nodes passively.
        It includes:
            what a node thinks about the cluster and
            total messages exchanged by the node up until this point.
        """
        self.global_state_map[ip] = epStateMap
        self.total_msg_count += msg_count

    def getSuspectMatrix(self):
        """
        Author: Ritesh G

        Used in front-end of Flask.
        """
        return self.suspect_matrix

    def doConsensus(self):
        """
        Author: Shreyas M

        Consensus Algorithm.    
        """

        print('---------------------------------------')
        for j in range(len(self.suspect_matrix[0])):
            state = 1
            for i in range(len(self.suspect_matrix)):
                if i != j and ((self.global_fault_vector[i]) != 1):
                    try:
                        if getDiffInSeconds(self.heartbeatTime[self.Index_to_IP[i]]) < Constants.WAIT_SECONDS_FAIL:
                            state &= self.suspect_matrix[i][j]
                    except Exception as e:
                        pass
            if(state == 1):
                print("Node %s is failed" % (self.Index_to_IP[j]))                
            else:
                print("Node %s is alive" % (self.Index_to_IP[j]))                
            self.global_fault_vector[j] = state
            if(state == 1):
                try:
                    self.ip_generation[j] = self.global_state_map[self.Index_to_IP[j]][self.Index_to_IP[j]]['heartBeat']['generation']
                except Exception as e:
                    pass
        print('---------------------------------------')


    def doConsensusCheck(self):
        """
        Author: Shreyas M

        Check Consensus.
        NOTE: This doesn't provide any external information to the nodes about 
              the status of nodes. It is just for presentation purpose to know
              what is happening inside the cluster.
        """
        res = True
        currentEpStateMap =  copy.deepcopy(self.global_state_map)
        for k,v in currentEpStateMap.items() :
            for k1, v1 in v.items():
                temp = {}
                temp['generation'] = v1['heartBeat']['generation']
                temp['App_status'] = v1['appState']['App_status']
                temp['App_version'] = v1['appState']['App_version']
                temp['fault_vector'] = self.suspect_matrix[self.IP_to_Node_Index[k]]
                self.consensusMap[k][k1] = temp

        # structure of consensus map
        # consensusMap = {k:{'App_version':v[], 'App_status':, 'generation':, 'fault_vector':}   }
        keyList = list(self.consensusMap.keys())
        temp = None
        for i in range(len(keyList)):
            if self.global_fault_vector[self.IP_to_Node_Index[keyList[i]]] != 1:
                if temp == None:
                    temp = self.consensusMap[keyList[i]]
                else:
                    res = res & (temp == self.consensusMap[keyList[i]])
                    temp = self.consensusMap[keyList[i]]
        return res

    def readFile(self):
        """
        Author: Ritesh G

        Used in front-end of Flask.
        """
        data = ""
        with open('results.txt', 'r') as fp:
            data = fp.read()
        data = data.replace('\n', '<br>')
        return data


if __name__ == "__main__":
    import socket
    import socket, dns.resolver,dns.reversename

    configuration_file,_ = get_arguments()
   

    os.environ["GOSSIP_CONFIG"] = configuration_file
    # ConfigurationManager.reset_configuration()
    configuration = Configuration(configuration_file)
    # Author: Tanvi P
    host_ip =  socket.gethostbyname(socket.gethostname())
    server_ip = str(dns.resolver.resolve_address(host_ip).rrset[0]).split('.')[0]
    server_port = configuration.get_gossip_port()
    
    # Author: Ritesh G
    node = MonitoringNode()
    start_gossip_node(node)
    
    import json

    while True:

        console_input = input("1. \"Test Case for Single Node failure\"\
                             \n2. \"Test Case for Simultaneous Failure\"\
                             \n3. \"Test Case for Dead Node becomes Alive\"\
                            \n4. \"stop\"\nEnter your input:")
        
        if console_input.strip() == "collect":
            with open('states.json','w') as fp:
                json.dump(node.global_state_map,fp)
            with open('ip_mapping.json', 'w') as fp:
                json.dump(node.IP_to_Node_Index, fp)
            
        
        

        
        if console_input.strip() == "1":
            # single node failure case
            node.start_time = time.perf_counter()  
            node.total_msg_count = 0
            node.false_failure_count = 0
            flag = 0
            while(1):
                for ip,status in enumerate(node.global_fault_vector):
                    ip = node.Index_to_IP[ip]
                    if status == 1 and (getDiffInSeconds(node.heartbeatTime[ip]) > Constants.WAIT_SECONDS_FAIL):
                        flag = 1        #consensus
                        break
                
                if flag:
                    run_time = time.perf_counter() - node.start_time 
                    with open('results.txt', 'a+') as file_pointer:
                        file_pointer.write('\n\n------------- Consensus Achieved --------------\n')
                        file_pointer.write('Test Case for Single Node failure\n')
                        file_pointer.write("Run time for detection: "+str(run_time)+'\n')
                        file_pointer.write("Total Messages exchanged for consensus: "+str(node.total_msg_count)+'\n') 
                        file_pointer.write("False Failure Detection Count: "+str(node.false_failure_count)+'\n')
                        file_pointer.write("Total number of nodes in cluster: "+str(len(node.Index_to_IP))+'\n')
                        file_pointer.close()
                    print('------------- Consensus Achieved --------------')
                    print("Run time for detection: ", run_time)
                    print("Total Messages exchanged for consensus: ", node.total_msg_count)  
                    print("False Failure Detection Count: ",node.false_failure_count)  
                    break          


        if console_input.strip() == "2":
            node.start_time = time.perf_counter()  
            node.total_msg_count = 0
            node.false_failure_count = 0
            while(1):
                if(node.doConsensusCheck()):
                    run_time = time.perf_counter() - node.start_time 
                    with open('results.txt', 'a+') as file_pointer:
                        file_pointer.write('\n\n------------- Consensus Achieved --------------\n')
                        file_pointer.write('Test Case for Simultaneous Failure\n')
                        file_pointer.write("Run time for detection: "+str(run_time)+'\n')
                        file_pointer.write("Total Messages exchanged for consensus"+str(node.total_msg_count)+'\n') 
                        file_pointer.write("False Failure Detection Count: "+str(node.false_failure_count)+'\n') 
                        file_pointer.write("Total number of nodes in cluster: "+str(len(node.Index_to_IP))+'\n')
                        file_pointer.close()
                    print('------------- Consensus Achieved --------------')
                    print("Run time for detection: ", run_time)
                    print("Total Messages exchanged for consensus", node.total_msg_count)  
                    print("False Failure Detection Count: ",node.false_failure_count)     
                    break       
                    # exit(0)

        if console_input.strip() == "3":
            node.start_time = time.perf_counter()  
            node.total_msg_count = 0
            node.false_failure_count = 0
            while(1):
                # if(len(list(set(list(result_dict.values())))) == 1):
                if(node.doConsensusCheck()):
                    run_time = time.perf_counter() - node.start_time 
                    with open('results.txt', 'a+') as file_pointer:
                        file_pointer.write('\n\n------------- Consensus Achieved --------------\n')
                        file_pointer.write('Test Case for Dead Node becomes Alive\n')
                        file_pointer.write("Run time for detection: "+str(run_time)+'\n')
                        file_pointer.write("Total Messages exchanged for consensus"+str(node.total_msg_count)+'\n') 
                        file_pointer.write("False Failure Detection Count: "+str(node.false_failure_count)+'\n') 
                        file_pointer.write("Total number of nodes in cluster: "+str(len(node.Index_to_IP))+'\n')
                        file_pointer.close()
                    print('------------- Consensus Achieved --------------')
                    print("Run time for detection: ", run_time)
                    print("Total Messages exchanged for consensus", node.total_msg_count)  
                    print("False Failure Detection Count: ",node.false_failure_count)     
                    break
                    # exit(0)



        if console_input.strip() == "4":
            stop_gossip_node()
            break