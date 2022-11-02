from nodes import Node
import hashlib
from random import random, seed
from config import Config

class Leader:

    def __init__(self, leaderNode : Node, globalObj):
        self.leaderNode = leaderNode
        self.globalObj = globalObj
        self.current_status = {}


    def find_nodes_to_put_file(self, sdfsFileName: str):
        hashObj = hashlib.sha256(sdfsFileName.encode('utf-8'))
        val = int.from_bytes(hashobj.digest(), 'big')
        
        nodes = []
        for i in range(4):
            val += int(random() * 100)
            id = (val % 10) + 1
            nodes.append(Config.get_node_from_id('H'+str(id)))

        return nodes

