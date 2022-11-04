from nodes import Node
import hashlib
from random import random, seed
from config import Config

class Leader:

    def __init__(self, leaderNode : Node, globalObj):
        self.leaderNode = leaderNode
        self.globalObj = globalObj
        self.current_status = {}
        # self.global_file_dict: dict = {
        #     "127.0.0.1:8001": {'Q1.jpg': ['Q1.jpg_version2', 'Q1.jpg_version3', 'Q1.jpg_version4', 'Q1.jpg_version5', 'Q1.jpg_version6']},
        #     "127.0.0.1:8002": {'Q1.jpg': ['Q1.jpg_version2', 'Q1.jpg_version3', 'Q1.jpg_version4', 'Q1.jpg_version5', 'Q1.jpg_version6']},
        #     "127.0.0.1:8003": {'Q1.jpg': ['Q1.jpg_version2', 'Q1.jpg_version3', 'Q1.jpg_version4', 'Q1.jpg_version5', 'Q1.jpg_version6']}
        # }

        self.global_file_dict: dict = {}
        self.status_dict: dict = {}
    
    def merge_files_in_global_dict(self, files_in_node, sender):

        self.global_file_dict[sender] = files_in_node

    def check_if_file_exists(self, sdfsFileName):

        for node in self.global_file_dict.keys():
            for file in self.global_file_dict[node].keys():
                if file == sdfsFileName:
                    return True
        
        return False
    
    def find_nodes_to_delete_file(self, sdfsFileName: str):
        nodes = []
        for node, node_file_dict in self.global_file_dict.items():
            if sdfsFileName in node_file_dict:
                nodes.append(node)
        return nodes

    def find_nodes_to_put_file(self, sdfsFileName: str):

        nodes = []
        if self.check_if_file_exists(sdfsFileName):
            for node in self.global_file_dict.keys():
                for file in self.global_file_dict[node].keys():
                    if file == sdfsFileName:
                        nodes.append(Config.get_node_from_unique_name(node))
                        break
            
        else:
            hashObj = hashlib.sha256(sdfsFileName.encode('utf-8'))
            val = int.from_bytes(hashObj.digest(), 'big')

            node_id_set = set()
            while len(node_id_set) < 4:
                val += int(random() * 100)
                id = (val % len(self.globalObj.worker.membership_list.memberShipListDict)) + 1
                node_id_set.add(id)
            
            for id in node_id_set:
                nodes.append(Config.get_node_from_id('H'+str(id)))

        return nodes
    
    def is_file_upload_inprogress(self, sdfsFileName):
        return sdfsFileName in self.status_dict

    def get_machineids_for_file(self, sdfsFileName) -> list:
        machineids = []
        for machineid, machine_file_dict in self.global_file_dict.items():
            if sdfsFileName in machine_file_dict:
                machineids.append(machineid)
        return machineids
    
    def get_machineids_with_filenames(self, sdfsFileName) -> dict:
        machineids_filenames = {}
        for machineid, machine_file_dict in self.global_file_dict.items():
            if sdfsFileName in machine_file_dict:
                machineids_filenames[machineid] = machine_file_dict[sdfsFileName]
        return machineids_filenames

    def create_new_status_for_file(self, filename: str, requestingNode: Node, request_type: str):
        self.status_dict[filename] = {
            'request_type': request_type,
            'request_node': requestingNode,
            'replicas': {}
        }

    def check_if_request_completed(self, filename):
        for key, item in self.status_dict[filename]['replicas'].items():
            if item != 'Success':
                return False
        return True
    
    def update_replica_status(self, sdfsFileName:str, replicaNode: Node, status: str):
        self.status_dict[sdfsFileName]['replicas'][replicaNode.unique_name] = status
    
    def add_replica_to_file(self, sdfsFileName: str, replicaNode: Node):
        self.status_dict[sdfsFileName]['replicas'][replicaNode.unique_name] = 'Waiting'