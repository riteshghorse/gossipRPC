from xmlrpc.server import SimpleXMLRPCServer
from collections import defaultdict
from gossip_server import get_arguments, start_gossip_node, stop_gossip_node
from configuration_manager import ConfigurationManager
import os
import time
import copy
from utils import *
import Constants

class MonitoringNode:
    def __init__(self):
        self.node_index = 0
        self.IP_to_Node_Index = {}
        self.Index_to_IP = {}
        self.suspect_matrix = [[]]
        self.global_fault_vector = []
        self.global_state_map = defaultdict(defaultdict)
        self.start_time = None
        self.node_msg_count = defaultdict()
        self.total_msg_count = 0
        self.consensusMap = defaultdict(defaultdict)
        self.ip_generation = defaultdict()
        self.heartbeatTime = {}

    def setheartbeatTime(self, ip):
        # print(ip, 'updating hb\n')
        self.heartbeatTime[ip] = getTimeStamp()

    def setMapping(self,ip):
        if ip in self.IP_to_Node_Index:
            return
        self.global_fault_vector.extend([0])
        self.IP_to_Node_Index[ip] = self.node_index
        self.Index_to_IP[self.node_index] = ip
        
        for row in self.suspect_matrix:
            row.extend([0])

        # print(self.suspect_matrix)
        if(len(self.suspect_matrix[0]) > 1):
            # self.suspect_matrix.append([0 for i in range(len(self.suspect_matrix[0]))])
            self.suspect_matrix.append(list(self.global_fault_vector))

        # print('\n') 
        self.node_index += 1

    def getMapping(self):
        return self.IP_to_Node_Index


    def updateSuspectMatrix(self, ip, fault_vector, generation):
        
        try:
            if self.global_fault_vector[self.IP_to_Node_Index[ip]] == 1:
                self.global_fault_vector[self.IP_to_Node_Index[ip]] = 0
            index = self.getMapping()[ip]
        except Exception as e:
            pass
        for k,v in fault_vector.items():
            if v==0:
                try:
                    if(self.IP_to_Node_Index[k] in self.ip_generation and generation == self.ip_generation[self.IP_to_Node_Index[k]]):
                        print('False failure detection happened for ', k)        
                except Exception as e:
                    pass
            
            self.suspect_matrix[self.IP_to_Node_Index[ip]][self.IP_to_Node_Index[k]] = v 
            
        print('in consensus', ip)
        self.doConsensus()

    def getFaultVector(self):
        return self.global_fault_vector

    def showAliveDeadNode(self):
        live_nodes = [self.Index_to_IP[ip] for ip,status in enumerate(self.global_fault_vector) if status!=1]
        dead_nodes = [self.Index_to_IP[ip] for ip,status in enumerate(self.global_fault_vector) if status==1]
        # return live_nodes
        return {'live': live_nodes, 'dead': dead_nodes}

    def sendEpStateMap(self, ip, epStateMap, msg_count):
        self.receiveStateMap(ip, epStateMap, msg_count)
        

    def receiveStateMap(self, ip, epStateMap, msg_count):
        self.global_state_map[ip] = epStateMap
        # self.node_msg_count[ip] += msg_count
        self.total_msg_count += msg_count



    def getSuspectMatrix(self):
        return self.suspect_matrix

    def doConsensus(self):
        for j in range(len(self.suspect_matrix[0])):
            state = 1
            # flag = 1
            for i in range(len(self.suspect_matrix)):
                if i != j and ((self.global_fault_vector[i]) != 1):
                    # print('first if')
                    try:
                        print('/// time: ', self.heartbeatTime[self.Index_to_IP[i]])
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

        print('end consensus')

    def doConsensusCheck(self):
        res = True
        # keyList = self.global_state_map.keys()
        currentEpStateMap =  copy.deepcopy(self.global_state_map)
        for k,v in currentEpStateMap.items() :
            for k1, v1 in v.items():
                temp = {}
                temp['generation'] = v1['heartBeat']['generation']
                temp['App_status'] = v1['appState']['App_status']
                temp['App_version'] = v1['appState']['App_version']
                # print(self.IP_to_Node_Index)
                temp['fault_vector'] = self.suspect_matrix[self.IP_to_Node_Index[k]]
                self.consensusMap[k][k1] = temp

        # consensusMap = {k:{'App_version':v[], 'App_status':, 'generation':, 'fault_vector':}   }
        keyList = list(self.consensusMap.keys())
        for i in range(len(keyList)-1):
            if self.global_fault_vector[self.IP_to_Node_Index[keyList[i]]] != 1:
                res = res & (self.consensusMap[keyList[i]] == self.consensusMap[keyList[i+1]])
        
        return res



if __name__ == "__main__":


    configuration_file = get_arguments()
   

    os.environ["GOSSIP_CONFIG"] = configuration_file
    ConfigurationManager.reset_configuration()

    server_ip = ConfigurationManager.get_configuration().get_gossip_host()
    server_port = ConfigurationManager.get_configuration().get_gossip_port()
    
    
    node = MonitoringNode()
    start_gossip_node(node)
    
    
    while True:

        console_input = input("1. \"stop\" \n2. \"check consensus\" \n 3. \"live node\" \n4. \"global suspect matrix\" \n5. \"fault vector\" \n6. start time"
                              "Enter your input:")
        
        if console_input.strip() == "stop":
            stop_gossip_node()
            break

        if console_input.strip() == "check":
            while(node.doConsensusCheck()):
                time.sleep(2)
            print('\n--------- check complete ------------')
            
            
        if console_input.strip() == "start":
            node.start_time = time.perf_counter()  
            while(1):
                result_dict = {}


                for k,v in node.global_state_map.items():
                    result_dict[k] = len(v)
                    
                # print(result_dict)
                # if(len(list(set(list(result_dict.values())))) == 1):
                if(node.doConsensusCheck()):
                    print('------------- Consensus Achieved --------------')
                    run_time = time.perf_counter() - node.start_time 
                    print(run_time)
                    print(node.total_msg_count)          
                    exit(0)

        if console_input.strip() == "live":
            print(node.getMapping().keys())

        if console_input.strip() == 'suspect':
            print(node.getSuspectMatrix())

        if console_input.strip() == 'fault':
            print(node.global_fault_vector)

        if console_input.strip() == 'consensus':
            node.doConsensus()


