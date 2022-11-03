from typing import final, List
from nodes import Node

M: final = 3

PING_TIMEOOUT: final = 2

PING_DURATION: final = 2.5

CLEANUP_TIME: final = 10

INTRODUCER_DNS_HOST = "127.0.0.1"
INTRODUCER_DNS_PORT = 8888

USERNAME = 'meghansh'
PASSWORD = ''

H1: final = Node('127.0.0.1', 8001, 'H1')
H2: final = Node('127.0.0.1', 8002, 'H2')
H3: final = Node('127.0.0.1', 8003, 'H3')
H4: final = Node('127.0.0.1', 8004, 'H4')
H5: final = Node('127.0.0.1', 8005, 'H5')
H6: final = Node('127.0.0.1', 8006, 'H6')
H7: final = Node('127.0.0.1', 8007, 'H7')
H8: final = Node('127.0.0.1', 8008, 'H8')
H9: final = Node('127.0.0.1', 8009, 'H9')
H10: final = Node('127.0.0.1', 8010, 'H10')

# Global nodes configuration
# ADD new nodes here...
# H1: final = Node('fa22-cs425-6901.cs.illinois.edu', 8000, 'H1')
# H2: final = Node('fa22-cs425-6902.cs.illinois.edu', 8000, 'H2')
# H3: final = Node('fa22-cs425-6903.cs.illinois.edu', 8000, 'H3')
# H4: final = Node('fa22-cs425-6904.cs.illinois.edu', 8000, 'H4')
# H5: final = Node('fa22-cs425-6905.cs.illinois.edu', 8000, 'H5')
# H6: final = Node('fa22-cs425-6906.cs.illinois.edu', 8000, 'H6')
# H7: final = Node('fa22-cs425-6907.cs.illinois.edu', 8000, 'H7')
# H8: final = Node('fa22-cs425-6908.cs.illinois.edu', 8000, 'H8')
# H9: final = Node('fa22-cs425-6909.cs.illinois.edu', 8000, 'H9')
# H10: final = Node('fa22-cs425-6910.cs.illinois.edu', 8000, 'H10')

# Current Ring topology
# Edit the ring as needed
GLOBAL_RING_TOPOLOGY: dict = {

    H1: [H2, H10, H5],

    H2: [H3, H1, H6],

    H3: [H4, H2, H7],

    H4: [H5, H3, H8],

    H5: [H6, H4, H9],

    H6: [H7, H5, H10],

    H7: [H8, H6, H1],

    H8: [H9, H7, H2],

    H9: [H10, H8, H3],

    H10: [H1, H9, H4]

}


class Config:
    """
    Config class which takes current hostname, port, introducer and testing flags from cmdline args. 
    """

    def __init__(self, hostname: str, port: int, testing: bool) -> None:

        self.node: Node = Config.get_node(hostname, port)
        self.ping_nodes: List[Node] = GLOBAL_RING_TOPOLOGY[self.node]
        self.introducerDNSNode = Node(INTRODUCER_DNS_HOST, INTRODUCER_DNS_PORT)
        # self.introducerNode = None
        # self.introducerFlag = False
        # self.introducerNode = Node(introducer.split(
        #     ":")[0], int(introducer.split(":")[1]))

        # if (self.node.unique_name == self.introducerNode.unique_name):
        #     self.introducerFlag = True
        # else:
        #     self.introducerFlag = False

        self.testing = testing

    

    @staticmethod
    def get_node(hostname: str, port: int) -> Node:
        """Return class Node which matches hostname and port"""
        member = None
        for node in GLOBAL_RING_TOPOLOGY.keys():
            if node.host == hostname and node.port == port:
                member = node
                break

        return member

    @staticmethod
    def get_node_from_unique_name(unique_name: str) -> Node:
        """Return class Node which matches unique name"""
        member = None
        for node in GLOBAL_RING_TOPOLOGY.keys():
            if node.unique_name == unique_name:
                member = node
                break

        return member

    @staticmethod
    def get_node_from_id(id: str):
        for node in GLOBAL_RING_TOPOLOGY.keys():
            if node.name == id:
                return node
        
        return None
