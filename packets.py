from enum import Enum
import logging
import pickle
import struct
import json
from typing import Optional


class PacketType(str, Enum):
    """Current packet types supported by failure detector"""
    PING = "0000"
    ACK = "0001"
    INTRODUCE = "0010"
    INTRODUCE_ACK = "0011"
    FETCH_INTRODUCER = "0100"
    FETCH_INTRODUCER_ACK = "0101"
    ELECTION = '0110'
    COORDINATE = '0111'
    COORDINATE_ACK = '1000'
    UPDATE_INTRODUCER = '1001'
    DOWNLOAD_FILE = '1010'
    DOWNLOAD_FILE_SUCCESS = '1011'
    DOWNLOAD_FILE_FAIL = '1100'
    PUT_REQUEST = '1101'


class Packet:
    """Custom packet type for failure detector"""

    def __init__(self, sender: str, packetType: PacketType, data: dict):
        self.data = data
        self.type = packetType
        self.sender = sender

    def pack(self) -> bytes:
        """Returns the bytes for packet"""
        jsondata = json.dumps(self.data)
        return struct.pack(f"i{255}s{4}si{2048}s", len(self.sender), self.sender.encode('utf-8'), self.type.encode('utf-8'), len(jsondata), jsondata.encode())

        # pickled = pickle.dumps(self, pickle.HIGHEST_PROTOCOL)
        # return pickled

    @staticmethod
    def unpack(recvPacket: bytes):
        """Converts the bytes to Packet class"""
        try:
            unpacked_tuple: tuple[bytearray] = struct.unpack(
                f"i{255}s{4}si{2048}s", recvPacket)
            sender = unpacked_tuple[1][:unpacked_tuple[0]].decode('utf-8')
            packetType = unpacked_tuple[2].decode('utf-8')
            data = unpacked_tuple[4][:unpacked_tuple[3]].decode('utf-8')

            # print(sender, packetType, data)
            return Packet(sender, PacketType(packetType), json.loads(data))
        except Exception as e:
            logging.error(f"unknown bytes: {e}")
            return None
