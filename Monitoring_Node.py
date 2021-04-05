from xmlrpc.server import SimpleXMLRPCServer
from collections import defaultdict
from gossip_server import get_arguments, start_gossip_node, stop_gossip_node
from configuration_manager import ConfigurationManager
import os
import time

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

    def setMapping(self,ip):
        
        # global node_index
        # global global_fault_vector
        # global Index_to_IP
        # global IP_to_Node_Index
        # global suspect_matrix

        if ip in self.IP_to_Node_Index:
            return
        self.global_fault_vector.extend([0])
        self.IP_to_Node_Index[ip] = self.node_index
        self.Index_to_IP[self.node_index] = ip
        for row in self.suspect_matrix:
            row.extend([0])

        if(len(self.suspect_matrix[0]) > 1):
            self.suspect_matrix.append([0 for i in range(len(self.suspect_matrix[0]))])
        print(self.suspect_matrix)
        # print(getMapping())
        print('\n') 
        self.node_index += 1

    def getMapping(self):
        return self.IP_to_Node_Index


    def updateSuspectMatrix(self, ip, fault_vector):
        
        index = getMapping()[ip]
        self.suspect_matrix[index] = fault_vector
        self.doConsensus()
        print(self.global_fault_vector)


    def sendEpStateMap(self, ip, epStateMap, msg_count):
        self.receiveStateMap(ip, epStateMap, msg_count)
        

    def receiveStateMap(self, ip, epStateMap, msg_count):
        self.global_state_map[ip] = epStateMap
        # self.node_msg_count[ip] += msg_count
        self.total_msg_count += msg_count
        print('message count', msg_count)
        # self.total_msg_count += ms



    def getSuspectMatrix(self):
        return self.suspect_matrix

    def doConsensus(self):
        for j in range(len(self.suspect_matrix[0])):
            state = 1
            for i in range(len(self.suspect_matrix)):
                if i != j:
                    state &= self.suspect_matrix[i][j]
            if(state == 1):
                print("Node %s is failed" % (self.Index_to_IP[j]))                
            else:
                print("Node %s is alive" % (self.Index_to_IP[j]))                
            self.global_fault_vector[j] = state

    
    # server = SimpleXMLRPCServer(("localhost", 8000), allow_none = True)
    # print("Listening on port 8000...")
    # server.register_function(setMapping, "setMapping")
    # server.register_function(getMapping, "getMapping")
    # server.register_function(updateSuspectMatrix, "updateSuspectMatrix")



if __name__ == "__main__":


    configuration_file = get_arguments()
   

    os.environ["GOSSIP_CONFIG"] = configuration_file
    ConfigurationManager.reset_configuration()

    server_ip = ConfigurationManager.get_configuration().get_gossip_host()
    server_port = ConfigurationManager.get_configuration().get_gossip_port()
    
    
    node = MonitoringNode()
    start_gossip_node(node)
    
    
    while True:

        # time.sleep(5)
        # node.sendSYN()

        # while flag:

        # t = threading.Timer(Constants.WAIT_SECONDS_HEARTBEAT, node.updateHearbeat()).start()

        # print("\n\nRunning with server id : " + str(server_id))
        console_input = input("1. \"stop\" \n2. \"check consensus\" \n 3. \"live node\" \n4. \"global suspect matrix\" \n5. \"fault vector\" \n6. start time"
                              "Enter your input:")
        
        if console_input.strip() == "stop":
            stop_gossip_node()
            break

        if console_input.strip() == "check":
            print('Node Address \t\t\t\t  State Map')
            print(node.global_state_map)
            result_dict = {}
            for k,v in node.global_state_map.items():
                result_dict[k] = len(v)
                
            print(result_dict)
            if(len(list(set(list(result_dict.values())))) == 1):
                print('------------- Consensus Achieved --------------')
                run_time = time.perf_counter() - node.start_time 
                print(run_time)
                print(node.total_msg_count)
                # print(sum(list(node.node_msg_count.values())))
            
            
        if console_input.strip() == "start":
            node.start_time = time.perf_counter()  
            while(1):
                result_dict = {}


                for k,v in node.global_state_map.items():
                    result_dict[k] = len(v)
                    
                print(result_dict)
                if(len(list(set(list(result_dict.values())))) == 1):
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
