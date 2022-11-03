from nodes import Node
import hashlib
from random import random, seed
from config import Config

class Leader:

    def __init__(self, leaderNode : Node, globalObj):
        self.leaderNode = leaderNode
        self.globalObj = globalObj
        self.current_status = {}
        self.global_file_dict: dict = {
            "127.0.0.1:8001": {'Q1.jpg': ['Q1.jpg_version2', 'Q1.jpg_version3', 'Q1.jpg_version4', 'Q1.jpg_version5', 'Q1.jpg_version6']},
            "127.0.0.1:8002": {'Q1.jpg': ['Q1.jpg_version2', 'Q1.jpg_version3', 'Q1.jpg_version4', 'Q1.jpg_version5', 'Q1.jpg_version6']},
            "127.0.0.1:8003": {'Q1.jpg': ['Q1.jpg_version2', 'Q1.jpg_version3', 'Q1.jpg_version4', 'Q1.jpg_version5', 'Q1.jpg_version6']}
        }

    def find_nodes_to_put_file(self, sdfsFileName: str):
        hashObj = hashlib.sha256(sdfsFileName.encode('utf-8'))
        val = int.from_bytes(hashObj.digest(), 'big')
        
        nodes = []
        for i in range(4):
            val += int(random() * 100)
            id = (val % len(self.globalObj.worker.membership_list.memberShipListDict)) + 1
            nodes.append(Config.get_node_from_id('H'+str(id)))

        return nodes

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