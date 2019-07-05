import os
import sys
import hashlib
import asyncio
import binascii
import struct

from better_bencode import dumps as bencode, loads as bdecode
import math
import random
from types import SimpleNamespace, TracebackType
from typing import (  # noqa
    Any,
    Coroutine,
    Generator,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)


class MessageType:
    REQUEST = 0
    DATA = 1
    REJECT = 2


BT_PROTOCOL = b"BitTorrent protocol"
BT_PROTOCOL_LEN = len(BT_PROTOCOL)
EXT_ID = 20
EXT_HANDSHAKE_ID = 0
EXT_HANDSHAKE_MESSAGE = bytes([EXT_ID, EXT_HANDSHAKE_ID]) + bencode({b"m": {b"ut_metadata": 1}})

BLOCK = math.pow(2, 14)
MAX_SIZE = BLOCK * 1000
BT_HEADER = b'\x13BitTorrent protocol\x00\x00\x00\x00\x00\x10\x00\x01'


def random_id(size=20):
    return random.getrandbits(size * 8).to_bytes(size, "big")

def get_ut_metadata(data):
    ut_metadata = b"ut_metadata"
    index = data.index(ut_metadata)+len(ut_metadata) + 1
    data = data[index:]
    return int(data[:data.index(b'e')])


def get_metadata_size(data):
    metadata_size = b"metadata_size"
    start = data.index(metadata_size) + len(metadata_size) + 1
    data = data[start:]
    return int(data[:data.index(b"e")])


class WirePeerClient:
    def __init__(self, infohash, ip, port, loop=None):
        if isinstance(infohash, str):
            infohash = binascii.unhexlify(infohash.upper())
        self.infohash = infohash
        self.peer_id = random_id()

        self.ip = ip
        self.port = port
        self.loop = loop if loop else asyncio.get_event_loop()

        self.writer = None
        self.reader = None

        self.ut_metadata = 0
        self.metadata_size = 0
        self.handshaked = False
        self.pieces_num = 0
        self.pieces_received_num = 0
        self.pieces = None

    async def _connect(self):
        if self.writer is None:
            self.reader, self.writer = await asyncio.open_connection(
                self.ip, self.port, loop=self.loop
            )

    def close(self):
        self.writer.close()

    def check_handshake(self, data):
        # Check BT Protocol Prefix
        if data[:20] != BT_HEADER[:20]:
            return False
        # Check InfoHash
        if data[28:48] != self.infohash:
            return False
        # Check support metadata exchange
        if data[25] != 16:
            return False
        return True

    def write_message(self, message):
        length = struct.pack(">I", len(message))
        self.writer.write(length + message)

    def request_piece(self, piece):
        msg = bytes([EXT_ID, self.ut_metadata]) + bencode({b"msg_type": 0, b"piece": piece})
        self.write_message(msg)

    def pieces_complete(self):
        metainfo = b''.join(self.pieces)

        if len(metainfo) != self.metadata_size:
            # Wrong size
            return None

        infohash = hashlib.sha1(metainfo).hexdigest()
        if binascii.unhexlify(infohash.upper()) != self.infohash:
            # Wrong infohash
            return None

        return bdecode(metainfo)

    async def work(self):
        await asyncio.wait_for(self._connect(), timeout=1)
        self.writer.write(BT_HEADER + self.infohash + self.peer_id)
        while True:
            if not self.handshaked:
                if self.check_handshake(await self.reader.readexactly(68)):
                    self.handshaked = True
                    # Send EXT Handshake
                    self.write_message(EXT_HANDSHAKE_MESSAGE)
                else:
                    return None

            total_message_length, msg_id = struct.unpack("!IB", await self.reader.readexactly(5))
            # Total message length contains message id length, remove it
            payload_length = total_message_length - 1
            payload = await self.reader.readexactly(payload_length)

            if msg_id != EXT_ID:
                continue
            extended_id, extend_payload = payload[0], payload[1:]
            if extended_id == 0 and not self.ut_metadata:
                # Extend handshake, receive ut_metadata and metadata_size
                try:
                    self.ut_metadata = get_ut_metadata(extend_payload)
                    self.metadata_size = get_metadata_size(extend_payload)
                except:
                    return None
                self.pieces_num = math.ceil(self.metadata_size / BLOCK)
                self.pieces = [False] * self.pieces_num
                self.request_piece(0)
                continue

            try:
                split_index = extend_payload.index(b"ee")+2
                info = bdecode(extend_payload[:split_index])
                if info[b'msg_type'] != MessageType.DATA:
                    return None
                if info[b'piece'] != self.pieces_received_num:
                    return None
                self.pieces[info[b'piece']] = extend_payload[split_index:]
            except:
                return None
            self.pieces_received_num += 1
            if self.pieces_received_num == self.pieces_num:
                return self.pieces_complete()
            else:
                self.request_piece(self.pieces_received_num)

    async def __aenter__(self) -> 'WirePeerClient':
        return self

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        await self.close()


async def get_metadata(infohash, ip, port, loop=None):
    if not loop:
        loop = asyncio.get_event_loop()

    client = WirePeerClient(infohash)
    await client.connect(ip, port, loop)
    return await client.work()
