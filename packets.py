from enum import Enum
import logging
import pickle
import struct
import json
from typing import Optional


class PacketType(str, Enum):
    """Current packet types supported by failure detector"""
    PING = "00000"
    ACK = "00001"
    INTRODUCE = "00010"
    INTRODUCE_ACK = "00011"
    FETCH_INTRODUCER = "00100"
    FETCH_INTRODUCER_ACK = "00101"
    ELECTION = '00110'
    COORDINATE = '00111'
    COORDINATE_ACK = '01000'
    UPDATE_INTRODUCER = '01001'
    DOWNLOAD_FILE = '01010'
    DOWNLOAD_FILE_SUCCESS = '01011'
    DOWNLOAD_FILE_FAIL = '01100'
    DELETE_FILE = '01101'
    DELETE_FILE_ACK = '01110'
    DELETE_FILE_NAK = '01111'
    GET_FILE = '10000'
    GET_FILE_SUCCESS = '10001'
    GET_FILE_FAIL = '10010'
    PUT_REQUEST = '10011'
    LIST_FILE_REQUEST = '10100'
    LIST_FILE_REQUEST_ACK = '10101'
    GET_FILE_REQUEST = '10110'
    GET_FILE_REQUEST_ACK = '10111'
    PUT_REQUEST_ACK = '11000'

class Packet:
    """Custom packet type for failure detector"""

    def __init__(self, sender: str, packetType: PacketType, data: dict):
        self.data = data
        self.type = packetType
        self.sender = sender

    def pack(self) -> bytes:
        """Returns the bytes for packet"""
        jsondata = json.dumps(self.data)
        return struct.pack(f"i{255}s{5}si{2048}s", len(self.sender), self.sender.encode('utf-8'), self.type.encode('utf-8'), len(jsondata), jsondata.encode())

        # pickled = pickle.dumps(self, pickle.HIGHEST_PROTOCOL)
        # return pickled

    @staticmethod
    def unpack(recvPacket: bytes):
        """Converts the bytes to Packet class"""
        try:
            unpacked_tuple: tuple[bytearray] = struct.unpack(
                f"i{255}s{5}si{2048}s", recvPacket)
            sender = unpacked_tuple[1][:unpacked_tuple[0]].decode('utf-8')
            packetType = unpacked_tuple[2].decode('utf-8')
            data = unpacked_tuple[4][:unpacked_tuple[3]].decode('utf-8')

            # print(sender, packetType, data)
            return Packet(sender, PacketType(packetType), json.loads(data))
        except Exception as e:
            logging.error(f"unknown bytes: {e}")
            return None
