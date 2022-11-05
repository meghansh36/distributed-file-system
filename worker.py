from datetime import datetime
import logging
import sys
import asyncio
from asyncio import Event, exceptions
from time import time
from weakref import WeakSet, WeakKeyDictionary
from typing import final, Final, NoReturn, Optional
from config import GLOBAL_RING_TOPOLOGY, Config, PING_TIMEOOUT, PING_DURATION, USERNAME, PASSWORD
from nodes import Node
from packets import Packet, PacketType
from protocol import AwesomeProtocol
from membershipList import MemberShipList
from leader import Leader
from globalClass import Global
from election import Election
from file_service import FileService
from os import path
import copy

class Worker:
    """Main worker class to handle all the failure detection and sends PINGs and ACKs to other nodes"""
    def __init__(self, io: AwesomeProtocol) -> None:
        self.io: Final = io
        self._waiting: WeakKeyDictionary[Node, WeakSet[Event]] = WeakKeyDictionary()
        self.config: Config = None
        self.membership_list: Optional[MemberShipList] = None
        self.is_current_node_active = True
        self.waiting_for_introduction = True
        self.total_pings_send = 0
        self.total_ack_missed = 0
        self.missed_acks_count = {}
        self.file_service = FileService()
        self.file_status = {}
        self._waiting_for_leader_event: Optional[Event] = None
        self._waiting_for_second_leader_event: Optional[Event] = None
        self.get_file_sdfsfilename = None
        self.get_file_machineids_with_file_versions = None

    def initialize(self, config: Config, globalObj: Global) -> None:
        """Function to initialize all the required class for Worker"""
        self.config = config
        globalObj.set_worker(self)
        self.globalObj = globalObj
        self.globalObj.set_election(Election(globalObj))
        # self.waiting_for_introduction = False if self.config.introducerFlag else True
        self.leaderFlag = False
        self.leaderObj: Leader = None
        self.leaderNode: Node= None
        self.fetchingIntroducerFlag = True
        self.temporary_file_dict = {}
        # if self.config.introducerFlag:
        #     self.leaderObj = Leader(self.config.node)
        #     self.leaderFlag = True
        #     self.leaderNode = self.config.node.unique_name

        self.membership_list = MemberShipList(
            self.config.node, self.config.ping_nodes, globalObj)
        
        self.io.testing = config.testing
    
    async def replica_file(self, req_node: Node, replicas: list[dict]):
        status = False
        filename = ""
        for replica in replicas:
            host = replica["hostname"]
            username = USERNAME
            password = PASSWORD
            file_locations = replica["file_paths"]
            filename = replica["filename"]
            status = await self.file_service.replicate_file(host=host, username=username, password=password, file_locations=file_locations, filename=filename)
            if status:
                logging.info(f'successfully replicated file {filename} from {host} requested by {req_node.unique_name}')
                response = {"filename": filename, "all_files": self.file_service.current_files}
                await self.io.send(req_node.host, req_node.port, Packet(self.config.node.unique_name, PacketType.REPLICATE_FILE_SUCCESS, response).pack())
                break
            else:
                logging.error(f'failed to replicate file {filename} from {host} requested by {req_node.unique_name}')
        
        if not status:
            response = {"filename": filename, "all_files": self.file_service.current_files}
            await self.io.send(req_node.host, req_node.port, Packet(self.config.node.unique_name, PacketType.REPLICATE_FILE_FAIL, response).pack())


    async def put_file(self, req_node: Node, host, username, password, file_location, filename):
        status = await self.file_service.download_file(host=host, username=username, password=password, file_location=file_location, filename=filename)
        if status:
            logging.info(f'successfully downloaded file {file_location} from {host} requested by {req_node.unique_name}')
            # download success sending sucess back to requester
            response = {"filename": filename, "all_files": self.file_service.current_files}
            await self.io.send(req_node.host, req_node.port, Packet(self.config.node.unique_name, PacketType.DOWNLOAD_FILE_SUCCESS, response).pack())
        else:
            logging.error(f'failed to download file {file_location} from {host} requested by {req_node.unique_name}')
            # download failed sending failure message back to requester
            response = {"filename": filename, "all_files": self.file_service.current_files}
            await self.io.send(req_node.host, req_node.port, Packet(self.config.node.unique_name, PacketType.DOWNLOAD_FILE_FAIL, response).pack())
    
    async def delete_file(self, req_node, filename):
        logging.debug(f"request from {req_node.host}:{req_node.port} to delete file {filename}")
        status = self.file_service.delete_file(filename)
        if status:
            logging.info(f"successfully deleted file {filename}")
            response = {"filename": filename, "all_files": self.file_service.current_files}
            await self.io.send(req_node.host, req_node.port, Packet(self.config.node.unique_name, PacketType.DELETE_FILE_ACK, response).pack())
        else:
            logging.error(f"failed to delete file {filename}")
            response = {"filename": filename, "all_files": self.file_service.current_files}
            await self.io.send(req_node.host, req_node.port, Packet(self.config.node.unique_name, PacketType.DELETE_FILE_NAK, response).pack())

    async def get_file(self, req_node, filename):
        logging.debug(f"request from {req_node.host}:{req_node.port} to get file {filename}")
        response = self.file_service.get_file_details(filename)
        if "latest_file" in response:
            logging.error(f"Failed to find the file {filename}")
            await self.io.send(req_node.host, req_node.port, Packet(self.config.node.unique_name, PacketType.GET_FILE_NAK, response).pack())
        else:
            logging.info(f"Found file {filename} locally")
            await self.io.send(req_node.host, req_node.port, Packet(self.config.node.unique_name, PacketType.GET_FILE_ACK, response).pack())

    def display_machineids_for_file(self, sdfsfilename, machineids):
        output = f"File {sdfsfilename} found in {len(machineids)} machines:\n"
        for recv_machineid in machineids:
            output += f"{recv_machineid}\n"
        print(output)
    
    def _add_waiting(self, node: Node, event: Event) -> None:
        """Function to keep track of all the unresponsive PINGs"""
        waiting = self._waiting.get(node)
        if waiting is None:
            self._waiting[node] = waiting = WeakSet()
        waiting.add(event)

    def _notify_waiting(self, node) -> None:
        """Notify the PINGs which are waiting for ACKs"""
        waiting = self._waiting.get(node)
        if waiting is not None:
            for event in waiting:
                event.set()

    async def _run_handler(self) -> NoReturn:
        """RUN the main loop which handles all the communication to external nodes"""
        
        while True:
            packedPacket, host, port = await self.io.recv()

            packet: Packet = Packet.unpack(packedPacket)
            if (not packet) or (not self.is_current_node_active):
                continue

            logging.debug(f'got data: {packet.data} from {host}:{port}')

            if packet.type == PacketType.ACK or packet.type == PacketType.INTRODUCE_ACK:
                curr_node: Node = Config.get_node_from_unique_name(
                    packet.sender)
                logging.debug(f'got ack from {curr_node.unique_name}')
                if curr_node:

                    if packet.type == PacketType.ACK:
                        self.membership_list.update(packet.data)
                    else:
                        self.membership_list.update(packet.data['membership_list'])
                        leader = packet.data['leader']
                        self.leaderNode = Config.get_node_from_unique_name(leader)

                    self.waiting_for_introduction = False
                    # self.membership_list.update(packet.data)
                    self.missed_acks_count[curr_node] = 0
                    self._notify_waiting(curr_node)

            elif packet.type == PacketType.FETCH_INTRODUCER_ACK:
                logging.debug(f'got fetch introducer ack from {self.config.introducerDNSNode.unique_name}')
                introducer = packet.data['introducer']
                if introducer == self.config.node.unique_name:
                    self.leaderObj = Leader(self.config.node, self.globalObj)
                    self.globalObj.set_leader(self.leaderObj)
                    self.leaderFlag = True
                    self.leaderNode = self.config.node
                    self.waiting_for_introduction = False
                    self.leaderObj.global_file_dict = copy.deepcopy(self.temporary_file_dict)
                    self.temporary_file_dict = {}
                    print("I BECAME THE LEADER ", self.leaderNode.unique_name)
                else:
                    self.leaderNode = Config.get_node_from_unique_name(introducer)
                    print("MY NEW LEADER IS", self.leaderNode.unique_name)

                self.fetchingIntroducerFlag = False
                self._notify_waiting(self.config.introducerDNSNode)

            elif packet.type == PacketType.PING or packet.type == PacketType.INTRODUCE:
                # print(f'{datetime.now()}: received ping from {host}:{port}')
                self.membership_list.update(packet.data)
                await self.io.send(host, port, Packet(self.config.node.unique_name, PacketType.ACK, self.membership_list.get()).pack())

            elif packet.type == PacketType.ELECTION:
                print('I GOT AN ELECTION PACKET')
                if not self.globalObj.election.electionPhase:
                    print('STARTING MY OWN ELECTIONNNN')
                    self.globalObj.election.initiate_election()
                else:
                    print('I will check if i am leader or not')
                    if self.globalObj.election.check_if_leader():
                        await self.send_coordinator_message()
            
            elif packet.type == PacketType.COORDINATE:
                self.globalObj.election.electionPhase = False
                self.leaderNode = Config.get_node_from_unique_name(host + ":" + f'{port}')
                print('MY NEW LEADER IS', host, port)
                response = {'all_files': self.file_service.current_files}
                await self.io.send(host, port, Packet(self.config.node.unique_name, PacketType.COORDINATE_ACK, response).pack())
            
            elif packet.type == PacketType.COORDINATE_ACK:
                files_in_node = packet.data['all_files']
                self.globalObj.election.coordinate_ack += 1
                self.temporary_file_dict[packet.sender] = files_in_node
                # self.leaderObj.merge_files_in_global_dict(files_in_node, host, port)

                if self.globalObj.election.coordinate_ack == len(self.membership_list.memberShipListDict.keys()) - 1:
                    print('I AM THE NEW LEADER NOWWWWWWWWW')
                    await self.update_introducer()
            
            elif packet.type == PacketType.REPLICATE_FILE:
                curr_node: Node = Config.get_node_from_unique_name(packet.sender)
                if curr_node:
                    data: dict = packet.data
                    replicas = data["replicas"]
                    logging.debug(f"request from {curr_node.host}:{curr_node.port} to replicate files from {machine_username}@{machine_hostname}:{machine_file_location}")
                    asyncio.create_task(self.replica_file(req_node=curr_node, replicas=replicas))
            
            elif packet.type == PacketType.REPLICATE_FILE_SUCCESS:
                pass

            elif packet.type == PacketType.REPLICATE_FILE_FAIL:
                pass

            elif packet.type == PacketType.DOWNLOAD_FILE:
                # parse packet and get all the required fields to download a file
                curr_node: Node = Config.get_node_from_unique_name(packet.sender)
                if curr_node:
                    data: dict = packet.data
                    machine_hostname = data["hostname"]
                    machine_username = USERNAME
                    machine_password = PASSWORD
                    machine_file_location = data["file_path"]
                    machine_filename = data["filename"]
                    logging.debug(f"request from {curr_node.host}:{curr_node.port} to download file from {machine_username}@{machine_hostname}:{machine_file_location}")
                    asyncio.create_task(self.put_file(curr_node, machine_hostname, machine_username, machine_password, machine_file_location, machine_filename))

            elif packet.type == PacketType.DOWNLOAD_FILE_SUCCESS:
                curr_node: Node = Config.get_node_from_unique_name(packet.sender)
                if curr_node:
                    data: dict = packet.data
                    sdfsFileName = data['filename']
                    all_files = data['all_files']
                    # update status dict
                    self.leaderObj.merge_files_in_global_dict(all_files, packet.sender)
                    self.leaderObj.update_replica_status(sdfsFileName, curr_node, 'Success')
                    if self.leaderObj.check_if_request_completed(sdfsFileName):
                        original_requesting_node = self.leaderObj.status_dict[sdfsFileName]['request_node']
                        await self.io.send(original_requesting_node.host, original_requesting_node.port, Packet(self.config.node.unique_name, PacketType.PUT_REQUEST_SUCCESS, {'filename': sdfsFileName}).pack())
                        self.leaderObj.delete_status_for_file(sdfsFileName)
            
            elif packet.type == PacketType.DELETE_FILE:
                curr_node: Node = Config.get_node_from_unique_name(packet.sender)
                if curr_node:
                    data: dict = packet.data
                    machine_filename = data["filename"]
                    await self.delete_file(curr_node, machine_filename)

            elif packet.type == PacketType.DELETE_FILE_ACK or packet.type == PacketType.DELETE_FILE_NAK:
                curr_node: Node = Config.get_node_from_unique_name(packet.sender)
                if curr_node:
                    data: dict = packet.data
                    sdfsFileName = data['filename']
                    all_files = data['all_files']
                    # update status dict
                    self.leaderObj.merge_files_in_global_dict(all_files, packet.sender)
                    self.leaderObj.update_replica_status(sdfsFileName, curr_node, 'Success')
                    if self.leaderObj.check_if_request_completed(sdfsFileName):
                        original_requesting_node = self.leaderObj.status_dict[sdfsFileName]['request_node']
                        await self.io.send(original_requesting_node.host, original_requesting_node.port, Packet(self.config.node.unique_name, PacketType.DELETE_FILE_REQUEST_SUCCESS, {'filename': sdfsFileName}).pack())
                        self.leaderObj.delete_status_for_file(sdfsFileName)

            elif packet.type == PacketType.GET_FILE:
                curr_node: Node = Config.get_node_from_unique_name(packet.sender)
                if curr_node:
                    data: dict = packet.data
                    machine_filename = data["filename"]
                    self.get_file(curr_node, machine_filename)

            elif packet.type == PacketType.PUT_REQUEST:
                curr_node: Node = Config.get_node_from_unique_name(packet.sender)
                if curr_node:
                    sdfsFileName = packet.data['filename']
                    if self.leaderObj.is_file_upload_inprogress(sdfsFileName):
                        await self.io.send(curr_node.host, curr_node.port, Packet(self.config.node.unique_name, PacketType.PUT_REQUEST_FAIL, {'filename': sdfsFileName, 'error': 'File upload already inprogress...'}).pack())
                    else:
                        download_nodes = self.leaderObj.find_nodes_to_put_file(sdfsFileName)
                        self.leaderObj.create_new_status_for_file(sdfsFileName, curr_node, 'PUT')
                        for node in download_nodes:
                            await self.io.send(node.host, node.port, Packet(self.config.node.unique_name, PacketType.DOWNLOAD_FILE, {'hostname': host, 'file_path': packet.data['file_path'], 'filename': sdfsFileName}).pack())
                            self.leaderObj.add_replica_to_file(sdfsFileName, node)
                        await self.io.send(curr_node.host, curr_node.port, Packet(self.config.node.unique_name, PacketType.PUT_REQUEST_ACK, {'filename': sdfsFileName}).pack())

            elif packet.type == PacketType.DELETE_FILE_REQUEST:
                curr_node: Node = Config.get_node_from_unique_name(packet.sender)
                if curr_node:
                    sdfsFileName = packet.data['filename']
                    if self.leaderObj.is_file_upload_inprogress(sdfsFileName):
                        await self.io.send(curr_node.host, curr_node.port, Packet(self.config.node.unique_name, PacketType.DELETE_FILE_REQUEST_FAIL, {'error': "File upload inprogress"}).pack())
                    else:
                        file_nodes = self.leaderObj.find_nodes_to_delete_file(sdfsFileName)
                        if len(file_nodes) == 0:
                            await self.io.send(curr_node.host, curr_node.port, Packet(self.config.node.unique_name, PacketType.DELETE_FILE_REQUEST_SUCCESS, {'filename': sdfsFileName}).pack())
                        else:
                            self.leaderObj.create_new_status_for_file(sdfsFileName, curr_node, 'DELETE')
                            for node in file_nodes:
                                await self.io.send(node.host, node.port, Packet(self.config.node.unique_name, PacketType.DELETE_FILE, {'filename': sdfsFileName}).pack())
                                self.leaderObj.add_replica_to_file(sdfsFileName, node)
                            await self.io.send(curr_node.host, curr_node.port, Packet(self.config.node.unique_name, PacketType.DELETE_FILE_REQUEST_ACK, {'filename': sdfsFileName}).pack())

            elif packet.type == PacketType.DELETE_FILE_REQUEST_ACK:
                filename = packet.data['filename']
                print(f'Leader successfully received DELETE request for file {filename}. waiting for nodes to delete the file...')
                if self._waiting_for_leader_event is not None:
                    self._waiting_for_leader_event.set()

            elif packet.type == PacketType.DELETE_FILE_REQUEST_FAIL:
                filename = packet.data['filename']
                error = packet.data['error']
                print(f'Failed to delete file {filename}: {error}')
                if self._waiting_for_leader_event is not None:
                    self._waiting_for_leader_event.set()
                
                if self._waiting_for_second_leader_event is not None:
                    self._waiting_for_second_leader_event.set()

            elif packet.type == PacketType.DELETE_FILE_REQUEST_SUCCESS:
                filename = packet.data['filename']
                print(f'FILE {filename} SUCCESSFULLY DELETED')

                if self._waiting_for_leader_event is not None:
                    self._waiting_for_leader_event.set()

                if self._waiting_for_second_leader_event is not None:
                    self._waiting_for_second_leader_event.set()

            elif packet.type == PacketType.PUT_REQUEST_ACK:
                filename = packet.data['filename']
                print(f'Leader successfully received PUT request for file {filename}. waiting for nodes to download the file...')
                if self._waiting_for_leader_event is not None:
                    self._waiting_for_leader_event.set()

            elif packet.type == PacketType.PUT_REQUEST_SUCCESS:
                filename = packet.data['filename']
                print(f'FILE {filename} SUCCESSFULLY STORED')

                if self._waiting_for_leader_event is not None:
                    self._waiting_for_leader_event.set()

                if self._waiting_for_second_leader_event is not None:
                    self._waiting_for_second_leader_event.set()

            elif packet.type == PacketType.PUT_REQUEST_FAIL:
                filename = packet.data['filename']
                error = packet.data['error']
                print(f'Failed to PUT file {filename}: {error}')
                if self._waiting_for_leader_event is not None:
                    self._waiting_for_leader_event.set()
                
                if self._waiting_for_second_leader_event is not None:
                    self._waiting_for_second_leader_event.set()

            elif packet.type == PacketType.LIST_FILE_REQUEST:
                curr_node: Node = Config.get_node_from_unique_name(packet.sender)
                if curr_node:
                    sdfsFileName = packet.data['filename']
                    machines = self.leaderObj.get_machineids_for_file(sdfsFileName)
                    await self.io.send(curr_node.host, curr_node.port, Packet(self.config.node.unique_name, PacketType.LIST_FILE_REQUEST_ACK, {'filename': sdfsFileName, 'machines': machines}).pack())

            elif packet.type == PacketType.LIST_FILE_REQUEST_ACK:
                recv_sdfsfilename = packet.data['filename']
                recv_machineids: list[str] = packet.data["machines"]
                self.display_machineids_for_file(recv_sdfsfilename, recv_machineids)
                if self._waiting_for_leader_event is not None:
                    self._waiting_for_leader_event.set()

            elif packet.type == PacketType.GET_FILE_REQUEST:
                curr_node: Node = Config.get_node_from_unique_name(packet.sender)
                if curr_node:
                    sdfsFileName = packet.data['filename']
                    machineids_with_filenames = self.leaderObj.get_machineids_with_filenames(sdfsFileName)
                    await self.io.send(curr_node.host, curr_node.port, Packet(self.config.node.unique_name, PacketType.GET_FILE_REQUEST_ACK, {'filename': sdfsFileName, 'machineids_with_file_versions': machineids_with_filenames}).pack())

            elif packet.type == PacketType.GET_FILE_REQUEST_ACK:
                self.get_file_sdfsfilename = packet.data['filename']
                self.get_file_machineids_with_file_versions = packet.data["machineids_with_file_versions"]
                if self._waiting_for_leader_event is not None:
                    self._waiting_for_leader_event.set()

    async def _wait(self, node: Node, timeout: float) -> bool:
        """Function to wait for ACKs after PINGs"""
        event = Event()
        self._add_waiting(node, event)

        try:
            await asyncio.wait_for(event.wait(), timeout)
        except exceptions.TimeoutError:
            # print(f'{datetime.now()}: failed to recieve ACK from {node.unique_name}')
            self.total_ack_missed += 1
            if not self.waiting_for_introduction and not self.fetchingIntroducerFlag:
                if node in self.missed_acks_count:
                    self.missed_acks_count[node] += 1
                else:
                    self.missed_acks_count[node] = 1
                
                logging.error(f'failed to recieve ACK from {node.unique_name} for {self.missed_acks_count[node]} times')
                if self.missed_acks_count[node] > 3:
                    self.membership_list.update_node_status(node=node, status=0)
            else:
                logging.error(f'failed to recieve ACK from {node.unique_name}')
                self.fetchingIntroducerFlag = True
        except Exception as e:
            self.total_ack_missed += 1
            # print(f'{datetime.now()}: Exception when waiting for ACK from {node.unique_name}: {e}')
            if not self.waiting_for_introduction and not self.fetchingIntroducerFlag:
                if node in self.missed_acks_count:
                    self.missed_acks_count[node] += 1
                else:
                    self.missed_acks_count[node] = 1

                logging.error(f'Exception when waiting for ACK from {node.unique_name} for {self.missed_acks_count[node]} times: {e}')
                if self.missed_acks_count[node] > 3:
                    self.membership_list.update_node_status(node=node, status=0)
            else:
                logging.error(
                    f'Exception when waiting for ACK from introducer: {e}')

        return event.is_set()

    async def _wait_for_leader(self, timeout: float) -> bool:
        """Function to wait for Leader to respond back for request"""
        event = Event()
        self._waiting_for_leader_event = event

        try:
            await asyncio.wait_for(event.wait(), timeout)
        except exceptions.TimeoutError:
            print(f'{datetime.now()}: failed to recieve Response from Leader')
        except Exception as e:
            print(f'{datetime.now()}: Exception when waiting for Response from Leader: {e}')

        return event.is_set()

    async def introduce(self) -> None:
        """FUnction to ask introducer to introduce"""
        logging.debug(
            f'sending pings to introducer: {self.leaderNode.unique_name}')
        await self.io.send(self.leaderNode.host, self.leaderNode.port, Packet(self.config.node.unique_name, PacketType.INTRODUCE, self.membership_list.get()).pack())
        await self._wait(self.leaderNode, PING_TIMEOOUT)

    async def fetch_introducer(self) -> None:
        logging.debug(f'sending pings to introducer DNS: {self.config.introducerDNSNode.unique_name}')
        print('sending ping to fetch introducer')
        await self.io.send(self.config.introducerDNSNode.host, self.config.introducerDNSNode.port, Packet(self.config.node.unique_name, PacketType.FETCH_INTRODUCER, {}).pack())
        await self._wait(self.config.introducerDNSNode, PING_TIMEOOUT)

    async def update_introducer(self):
        print('updating introducer on DNS')
        await self.io.send(self.config.introducerDNSNode.host, self.config.introducerDNSNode.port, Packet(self.config.node.unique_name, PacketType.UPDATE_INTRODUCER, {}).pack())
        await self._wait(self.config.introducerDNSNode, PING_TIMEOOUT)

    async def check(self, node: Node) -> None:
        """Fucntion to send PING to a node"""
        logging.debug(f'pinging: {node.unique_name}')
        await self.io.send(node.host, node.port, Packet(self.config.node.unique_name, PacketType.PING, self.membership_list.get()).pack())
        await self._wait(node, PING_TIMEOOUT)

    async def send_election_messages(self):
        while True:
            if self.globalObj.election.electionPhase:
                for node in self.membership_list.current_pinging_nodes:
                    print(f'sending election message to {node.unique_name}')
                    await self.io.send(node.host, node.port, Packet(self.config.node.unique_name, PacketType.ELECTION, {}).pack())

            await asyncio.sleep(PING_DURATION)
    
    async def send_coordinator_message(self):
        self.temporary_file_dict = {}
        online_nodes = self.membership_list.get_online_nodes()

        for node in online_nodes:
            if node.unique_name != self.config.node.unique_name :
                await self.io.send(node.host, node.port, Packet(self.config.node.unique_name, PacketType.COORDINATE, {}).pack())
            # await self._wait(node, PING_TIMEOOUT)

    async def run_failure_detection(self) -> NoReturn:
        """Function to sends pings to subset of nodes in the RING"""
        while True:
            if self.is_current_node_active:
                if not self.waiting_for_introduction:
                    for node in self.membership_list.current_pinging_nodes:
                        self.total_pings_send += 1
                        asyncio.create_task(self.check(node))
                else:
                    self.total_pings_send += 1
                    print(self.fetchingIntroducerFlag)
                    if self.fetchingIntroducerFlag:
                        asyncio.create_task(self.fetch_introducer())
                    print(self.waiting_for_introduction, self.fetchingIntroducerFlag)
                    if self.waiting_for_introduction and not self.fetchingIntroducerFlag:
                        print('i entered here now')
                        asyncio.create_task(self.introduce())

            await asyncio.sleep(PING_DURATION)

    async def send_put_request_to_leader(self, localFileName, sdfsFileName):
        await self.io.send(self.leaderNode.host, self.leaderNode.port, Packet(self.config.node.unique_name, PacketType.PUT_REQUEST, {'file_path': localFileName, 'filename': sdfsFileName}).pack())
        await self._wait_for_leader(20)

    async def send_del_request_to_leader(self, sdfsFileName):
        await self.io.send(self.leaderNode.host, self.leaderNode.port, Packet(self.config.node.unique_name, PacketType.DELETE_FILE_REQUEST, {'filename': sdfsFileName}).pack())
        await self._wait_for_leader(20)

    async def send_ls_request_to_leader(self, sdfsfilename):
        await self.io.send(self.leaderNode.host, self.leaderNode.port, Packet(self.config.node.unique_name, PacketType.LIST_FILE_REQUEST, {'filename': sdfsfilename}).pack())
        await self._wait_for_leader(20)
    
    async def send_get_file_request_to_leader(self, sdfsfilename):
        await self.io.send(self.leaderNode.host, self.leaderNode.port, Packet(self.config.node.unique_name, PacketType.GET_FILE_REQUEST, {'filename': sdfsfilename}).pack())
        await self._wait_for_leader(20)

    def isCurrentNodeLeader(self):
        if self.leaderObj is not None and self.config.node.unique_name == self.leaderNode.unique_name:
            return True
        return False

    async def handle_failures_if_pending_status(self, node: str):
        # TODO
        if self.leaderFlag:
            self.leaderObj.delete_node_from_global_dict(node)
        pass

    async def replicate_files(self):
        # TODO
        # leader node will find out the unique files in the system.
        # for each unique file, find the array of nodes
        # if file doesnt have 4 nodes, choose the missing number of nodes randomly
        if self.leaderFlag:
            replication_dict = self.leaderObj.find_files_for_replication()
            print(replication_dict)
            pass

    async def get_file_locally(self, machineids_with_filenames, sdfsfilename, localfilename, file_count=1):
        # download latest file locally
        if self.config.node.unique_name in machineids_with_filenames:
            if file_count == 1:
                filepath = self.file_service.copyfile(machineids_with_filenames[self.config.node.unique_name][-1], localfilename)
                print(f"GET file {sdfsfilename} success: copied to {filepath}")
            else:
                files = machineids_with_filenames[self.config.node.unique_name]
                filepaths = []
                if file_count > len(files):
                    file_count = len(files)
                for i in range(0, file_count):
                    filepath = self.file_service.copyfile(machineids_with_filenames[self.config.node.unique_name][len(files) - 1 - i], f'{localfilename}_version{i}')
                    filepaths.append(filepath)
                print(f"GET files {sdfsfilename} success: copied to {filepaths}")
        else:
            # file not in local system, download files from machines
            downloaded = False
            for machineid, files in machineids_with_filenames.items():
                download_node = self.config.get_node_from_unique_name(machineid)
                if file_count == 1:
                    downloaded = await self.file_service.download_file_to_dest(host=download_node.host, username=USERNAME, password=PASSWORD, file_location=files[-1], destination_file=localfilename)
                else:
                    if file_count > len(files):
                        file_count = len(files)
                    for i in range(0, file_count):
                        downloaded = await self.file_service.download_file_to_dest(host=download_node.host, username=USERNAME, password=PASSWORD, file_location=files[len(files) - 1 - i], destination_file=f'{localfilename}_version{i}')
                if downloaded:
                    print(f"GET file {sdfsfilename} success: copied to {localfilename}")
                    break
            if not downloaded:
                print(f"GET file {sdfsfilename} failed")
    
    async def check_user_input(self):
        """Function to ask for user input and handles"""
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def response():
            loop.create_task(queue.put(sys.stdin.readline()))

        loop.add_reader(sys.stdin.fileno(), response)

        while True:

            print(f'choose one of the following options or type commands:')
            print('options:')
            print(' 1. list the membership list.')
            print(' 2. list self id.')
            print(' 3. join the group.')
            print(' 4. leave the group.')
            if self.config.testing:
                print('5. print current bps.')
                print('6. current false positive rate.')
            print('commands:')
            print(' * put <localfilename> <sdfsfilename>')
            print(' * get <sdfsfilename> <localfilename>')
            print(' * delete <sdfsfilename>')
            print(' * ls <sdfsfilename>')
            print(' * store')
            print(' * get-versions <sdfsfilename> <numversions> <localfilename>')
            print('')

            option: Optional[str] = None
            while True:
                option = await queue.get()
                if option != '\n':
                    break
            
            if option.strip() == '1':
                self.membership_list.print()
                if self.leaderFlag:
                    print(self.leaderObj.global_file_dict)
            elif option.strip() == '2':
                print(self.config.node.unique_name)
            elif option.strip() == '3':
                self.is_current_node_active = True
                logging.info('started sending ACKs and PINGs')
            elif option.strip() == '4':
                self.is_current_node_active = False
                self.membership_list.memberShipListDict = dict()
                self.config.ping_nodes = GLOBAL_RING_TOPOLOGY[self.config.node]
                self.waiting_for_introduction = True
                self.io.time_of_first_byte = 0
                self.io.number_of_bytes_sent = 0
                # self.initialize(self.config)
                logging.info('stopped sending ACKs and PINGs')
            elif self.config.testing and option.strip() == '5':
                if self.io.time_of_first_byte != 0:
                    logging.info(
                        f'BPS: {(self.io.number_of_bytes_sent)/(time() - self.io.time_of_first_byte)}')
                else:
                    logging.info(f'BPS: 0')
            elif self.config.testing and option.strip() == '6':
                if self.membership_list.false_positives > self.membership_list.indirect_failures:
                    logging.info(
                        f'False positive rate: {(self.membership_list.false_positives - self.membership_list.indirect_failures)/self.total_pings_send}, pings sent: {self.total_pings_send}, indirect failures: {self.membership_list.indirect_failures}, false positives: {self.membership_list.false_positives}')
                else:
                    logging.info(
                        f'False positive rate: {(self.membership_list.indirect_failures - self.membership_list.false_positives)/self.total_pings_send}, pings sent: {self.total_pings_send}, indirect failures: {self.membership_list.indirect_failures}, false positives: {self.membership_list.false_positives}')
            else: # checking if user typed cmd
                option = option.strip()
                options = option.split(' ')
                if len(options) == 0:
                    print('invalid option.')
                cmd = options[0]

                if cmd == "put": # PUT file
                    if len(options) != 3:
                        print('invalid options for put command.')
                        continue
                    
                    localfilename = options[1]
                    if not path.exists(localfilename):
                        print('invalid localfilename for put command.')
                        continue
                    sdfsfilename = options[2]

                    await self.send_put_request_to_leader(localfilename, sdfsfilename)

                    event = Event()
                    self._waiting_for_second_leader_event = event
                    await asyncio.wait([self._waiting_for_second_leader_event.wait()])
                    del self._waiting_for_second_leader_event
                    self._waiting_for_second_leader_event = None
                    

                elif cmd == "get": # GET file
                    if len(options) != 3:
                        print('invalid options for get command.')
                        continue

                    sdfsfilename = options[1]
                    localfilename = options[2]
                    if self.isCurrentNodeLeader():
                        logging.info(f"fetching machine details locally about {sdfsfilename}.")
                        machineids_with_filenames = self.leaderObj.get_machineids_with_filenames(sdfsfilename)
                        await self.get_file_locally(machineids_with_filenames=machineids_with_filenames, sdfsfilename=sdfsfilename, localfilename=localfilename)
                    else:
                        logging.info(f"fetching machine details where the {sdfsfilename} is stored from Leader.")
                        await self.send_get_file_request_to_leader(sdfsfilename)
                        if self.get_file_machineids_with_file_versions is not None and self.get_file_sdfsfilename is not None:
                            await self.get_file_locally(machineids_with_filenames=self.get_file_machineids_with_file_versions, sdfsfilename=self.get_file_sdfsfilename, localfilename=localfilename)
                            self.get_file_machineids_with_file_versions = None
                            self.get_file_sdfsfilename = None

                        del self._waiting_for_leader_event
                        self._waiting_for_leader_event = None
                        print("get: done!!!")

                elif cmd == "delete": # DEL file
                    if len(options) != 2:
                        print('invalid options for delete command.')
                        continue

                    sdfsfilename = options[1]
                    await self.send_del_request_to_leader(sdfsfilename)

                    event = Event()
                    self._waiting_for_second_leader_event = event
                    await asyncio.wait([self._waiting_for_second_leader_event.wait()])
                    del self._waiting_for_second_leader_event
                    self._waiting_for_second_leader_event = None
                
                elif cmd == "ls": # list all the
                    if len(options) != 2:
                        print('invalid options for ls command.')
                        continue

                    sdfsfilename = options[1]
                    if self.isCurrentNodeLeader():
                        machineids = self.leaderObj.get_machineids_for_file(sdfsfilename)
                        self.display_machineids_for_file(sdfsfilename, machineids)
                    else:
                        await self.send_ls_request_to_leader(sdfsfilename)
                        del self._waiting_for_leader_event
                        self._waiting_for_leader_event = None

                elif cmd == "store": # store
                    self.file_service.list_all_files()

                elif cmd == "get-versions": # get-versions
                    if len(options) != 4:
                        print('invalid options for get-versions command.')
                        continue

                    sdfsfilename = options[1]
                    numversions = int(options[2])
                    localfilename = options[3]

                    if self.isCurrentNodeLeader():
                        logging.info(f"fetching machine details locally about {sdfsfilename}.")
                        machineids_with_filenames = self.leaderObj.get_machineids_with_filenames(sdfsfilename)
                        await self.get_file_locally(machineids_with_filenames=machineids_with_filenames, sdfsfilename=sdfsfilename, localfilename=localfilename, file_count=numversions)
                    else:
                        logging.info(f"fetching machine details where the {sdfsfilename} is stored from Leader.")
                        await self.send_get_file_request_to_leader(sdfsfilename)
                        if self.get_file_machineids_with_file_versions is not None and self.get_file_sdfsfilename is not None:
                            await self.get_file_locally(machineids_with_filenames=self.get_file_machineids_with_file_versions, sdfsfilename=self.get_file_sdfsfilename, localfilename=localfilename, file_count=numversions)
                            self.get_file_machineids_with_file_versions = None
                            self.get_file_sdfsfilename = None

                        del self._waiting_for_leader_event
                        self._waiting_for_leader_event = None
                        print("get-versions: done!!!")

                else:
                    print('invalid option.')

    @final
    async def run(self) -> NoReturn:
        await asyncio.gather(
            self._run_handler(),
            self.run_failure_detection(),
            self.check_user_input(),
            self.send_election_messages()
            )
        raise RuntimeError()
