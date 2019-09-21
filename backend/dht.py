import asyncio
import binascii
import sys
from time import time
import signal
from collections import Counter
import functools

import logging
import socket
from socket import inet_ntoa, gethostbyname
from struct import unpack

import better_bencode
import random
from backend.ipinfo import getCountryCode


class ServerError(Exception):
    pass


class ProtocolError(Exception):
    pass


def proper_infohash(infohash):
    if isinstance(infohash, bytes):
        # Convert bytes to hex
        infohash = binascii.hexlify(infohash).decode('utf-8')
    return infohash.upper()


def random_node_id(size=20):
    return random.getrandbits(size * 8).to_bytes(size, "big")


def split_nodes(nodes):
    length = len(nodes)
    if (length % 26) != 0:
        return

    for i in range(0, length, 26):
        nid = nodes[i:i+20]
        ip = inet_ntoa(nodes[i+20:i+24])
        port = unpack("!H", nodes[i+24:i+26])[0]
        yield nid, ip, port


__version__ = '3.0.0'


BOOTSTRAP_NODES = (
    ('dht.libtorrent.org', 25401),
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881),
    ("dht.aelitis.com", 6881),
)

BOOTSTRAP_NODES = [(gethostbyname(x), y) for (x,y) in BOOTSTRAP_NODES]

ALLOW_COUNTRIES = {'CN', 'HK', 'TW'}


class DHT(asyncio.DatagramProtocol):
    def __init__(self, loop=None, bootstrap_nodes=BOOTSTRAP_NODES, interval=1):
        self.node_id = random_node_id()
        self.transport = None
        self.loop = loop or asyncio.get_event_loop()
        self.bootstrap_nodes = bootstrap_nodes
        self.running = True
        self.interval = interval

    def stop(self):
        self.running = False
        for task in asyncio.Task.all_tasks():
            task.cancel()

    async def run(self, port=6881):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        transport, _ = await self.loop.create_datagram_endpoint(
                lambda: self, sock=s
        )

        for signame in ('SIGINT', 'SIGTERM'):
            try:
                self.loop.add_signal_handler(getattr(signal, signame), self.stop)
            except NotImplementedError:
                # SIGINT and SIGTERM are not implemented on windows
                pass

        while self.running:
            for node in self.bootstrap_nodes:
                self.find_node(addr=node)
            await asyncio.sleep(self.interval)

        transport.close()

    def datagram_received(self, data, addr):

        try:
            msg = better_bencode.loads(data)

        except Exception as e: # (better_bencode.BencodeTypeError, better_bencode.BencodeValueError):
            logging.warning(e)
            return

        if not isinstance(msg, dict):
            return

        try:
            self.handle_message(msg, addr)
        except ProtocolError:
            logging.warning('protocal error', addr, msg)
            self.send_message(
                data={
                    b"t": msg[b"t"],
                    b"y": b"e",
                    b"e": [203, b"Protocal Error"]
                },
                addr=addr)
        except Exception as e:
            logging.warning(e)
            self.send_message(data={
                b"t": msg[b"t"],
                b"y": b"e",
                b"e": [202, b"Server Error"]
            }, addr=addr)

    def handle_message(self, msg, addr):
        msg_type = msg.get(b"y", b"e")

        if msg_type == b"e":
            return

        if msg_type == b"r":
            if b"r" not in msg_type:
                raise ProtocolError
            return self.handle_response(msg, addr=addr)

        if msg_type == b'q':
            return asyncio.ensure_future(
                self.handle_query(msg, addr=addr), loop=self.loop
            )

    def handle_response(self, msg, addr):
        args = msg[b"r"]
        if b"nodes" in args:
            for node_id, ip, port in split_nodes(args[b"nodes"]):
                self.ping(addr=(ip, port))

    async def handle_query(self, msg, addr):
        args = msg[b"a"]
        node_id = args[b"id"]
        query_type = msg[b"q"]
        if query_type == b"get_peers":
            infohash = args[b"info_hash"]
            infohash = proper_infohash(infohash)
            token = infohash[:2].encode('utf-8')
            self.send_message({
                b"t": msg[b"t"],
                b"y": b"r",
                b"r": {
                    b"id": self.fake_node_id(node_id),
                    b"nodes": b"",
                    b"token": token
                }
            }, addr=addr)
            await self.handle_get_peers(infohash, addr)
        elif query_type == b"announce_peer":
            infohash = args[b"info_hash"]
            tid = msg[b"t"]
            self.send_message({
                b"t": tid,
                b"y": b"r",
                b"r": {
                    b"id": self.fake_node_id(node_id)
                }
            }, addr=addr)
            peer_addr = [addr[0], addr[1]]
            try:
                peer_addr[1] = args[b"port"]
            except KeyError:
                pass
            await self.handle_announce_peer(proper_infohash(infohash), addr, peer_addr)
        elif query_type == b"find_node":
            tid = msg[b"t"]
            self.send_message({
                b"t": tid,
                b"y": b"r",
                b"r": {
                    b"id": self.fake_node_id(node_id),
                    b"nodes": b""
                }
            }, addr)
        elif query_type == b"ping":
            if addr[0] not in {'0.0.0.0', '127.0.0.1'} and getCountryCode(addr[0]) in ALLOW_COUNTRIES:
                self.send_message({
                    b"t": b"tt",
                    b"y": b"r",
                    b"r": {
                        b"id": self.fake_node_id(node_id)
                    }
                }, addr)

        if addr[0] not in {'0.0.0.0', '127.0.0.1'} and getCountryCode(addr[0]) in ALLOW_COUNTRIES:
            self.find_node(addr=addr, node_id=node_id)

    def ping(self, addr, node_id=None):
        if addr[0] not in {'0.0.0.0', '127.0.0.1'} and getCountryCode(addr[0]) in ALLOW_COUNTRIES:
            self.send_message({
                b"y": b"q",
                b"t": b"pg",
                b"q": b"ping",
                b"a": {
                    b"id": self.fake_node_id(node_id)
                }
            }, addr)

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.running = False
        self.transport.close()

    def send_message(self, data, addr):
        data.setdefault(b"t", b"tt")
        try:
            msg = better_bencode.dumps(data)
            self.transport.sendto(msg, addr)
        except:
          logging.warning(data)

    def fake_node_id(self, node_id=None):
        if node_id:
            return (node_id[:-1]+self.node_id[-1:])
        return self.node_id

    @functools.lru_cache(maxsize=2048)
    def find_node(self, addr, node_id=None, target=None):
        if not target:
            target = random_node_id()
        self.send_message({
            b"t": b"aa",
            b"y": b"q",
            b"q": b"find_node",
            b"a": {
                b"id": self.fake_node_id(node_id),
                b"target": target,
            }
        }, addr)

    async def handle_get_peers(self, infohash, addr):
        await self.handler(infohash, addr, None, 'get_peers')

    async def handle_announce_peer(self, infohash, addr, peer_addr):
        await self.handler(infohash, addr, peer_addr, 'announce_peer')


class FakeDHT(DHT):
    def __init__(self):
        super(FakeDHT, self).__init__()
        self.get_peers_counter = 1
        self.announce_peer_counter = 1
        self.start_time = time()

    async def handler(self, infohash, addr, peer_addr, reason):
        if reason == 'get_peers':
            self.get_peers_counter += 1
        elif reason == 'announce_peer':
            self.announce_peer_counter += 1

        if self.get_peers_counter % 10000 == 0:
            elsape = time() - self.start_time
            logging.debug('handle_receive')
            logging.debug('\t'.join(['%s: %.3fb/s' % (k, v / elsape) for k, v in self.receive_counter.items()]))
            logging.debug('send')
            logging.debug('\t'.join(['%s: %.3fb/s' % (k, v / elsape) for k, v in self.send_counter.items()]))

            self.send_counter = Counter()
            self.receive_counter = Counter()
            self.start_time = time()


if __name__ == '__main__':

    dht_server = FakeDHT()
    asyncio.get_event_loop().run_until_complete(dht_server.run(sys.argv[1]))