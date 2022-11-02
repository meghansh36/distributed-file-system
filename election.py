from globalClass import Global
import asyncio
from config import Config

class Election:


    def __init__(self, globalObj: Global):
        self.globalObj = globalObj
        self.highestElectionID = None
        self.electionPhase = False
        self.coordinate_ack = 0

    def initiate_election(self):
        self.electionPhase = True
        self.globalObj.worker.leaderNode = None
        print('ELECTION INITIATEDDDD')
        # while self.electionPhase:
        #     asyncio.gather(self.globalObj.worker.send_election_messages())
    
    def check_if_leader(self):
        node = self.globalObj.worker.config.node
        my_id = int(node.name.strip('H'))
        print('my id is', my_id)

        for key in self.globalObj.worker.membership_list.memberShipListDict.keys():
            if key != node.unique_name:
                # check if any is bigger than me
                comparison_node = Config.get_node_from_unique_name(key)
                comparison_node_id = int(comparison_node.name.strip('H'))
                if comparison_node_id > my_id:
                    return False
        
        self.electionPhase = False
        self.coordinate_ack = 0
        return True
            