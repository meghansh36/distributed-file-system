from globalClass import Global

class Election:


    def __init__(self, globalObj: Global):
        self.globalObj = globalObj
        self.highestElectionID = None

    def initiate_election(self):
        self.highestElectionID = self.globalObj.worker.config.node.unique_name
        # on receiving an election msg, everyone will remove the leader from their worker objects and membership lists first. Do a topology change and then 
        self.globalObj.worker.send_election_message(nextNode)