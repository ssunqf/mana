import asyncio
import random
import socket
import struct
import time
import itertools
from typing import Dict
from collections import namedtuple

import requests
from util.database import Torrent

CONNECT = 0
ANNOUNCE = 1
SCRAPE = 2
ERROR = 3
BATCH_SIZE = 74
MAX_NUM_TIMEOUT = 10

TrackerInfo = namedtuple('TrackerInfo', ['host', 'ip', 'port'])


class TrackerClient:
    def __init__(self, info: TrackerInfo, transport, infohashes, loop):
        self.info = info
        self.transport = transport
        self.infohashes = infohashes

        self.transaction_id = None
        self.connection_id = None
        self.connection_time = None

        self.loop = loop
        self.timeout_handler = None
        self.num_timeout = 0
        self.offset = 0
        self.results = []

        self.finished = False

    def need_connect(self):
        return self.connection_id is None or time.time() - self.connection_time >= 55

    def timeout(self):
        if self.num_timeout < MAX_NUM_TIMEOUT:
            self.num_timeout += 1
            self.connect_request()
        else:
            self.finished = True

    def connect_request(self):
        # Protocol says to keep it that way4
        protocol_id = 0x41727101980

        # We should get the same in response
        transaction_id = random.randrange(1, 65535)

        # Send a Connect Request
        message = struct.pack(">QLL", protocol_id, 0, transaction_id)

        self.transaction_id = transaction_id
        self.transport.sendto(message, (self.info.ip, self.info.port))
        self.timeout_handler = self.loop.call_later(2, self.timeout)

    def connect_response(self, message):
        self.timeout_handler.cancel()

        assert len(message) == 8
        connection_id = struct.unpack(">Q", message)[0]

        self.connection_id = connection_id
        self.connection_time = time.time()

    def scrape_request(self):
        if len(self.results) >= len(self.infohashes):
            self.finished = True
            return

        message = struct.pack(">QLL", self.connection_id, 2, self.transaction_id)

        offset = len(self.results)
        for infohash in self.infohashes[offset:offset+BATCH_SIZE]:
            message += bytes.fromhex(infohash)

        self.transport.sendto(message, (self.info.ip, self.info.port))
        self.timeout_handler = self.loop.call_later(2, self.timeout)

    def scrape_response(self, message):
        self.timeout_handler.cancel()

        assert len(message) % 12 == 0
        batch = self.infohashes[self.offset:self.offset+BATCH_SIZE]
        for infohash, offset in zip(batch, range(0, len(message), 12)):
            seeders, completed, leechers = struct.unpack(">LLL", message[offset:offset+12])
            self.results.append((infohash, seeders, completed, leechers))

        self.offset += len(batch)

    def handle_receive(self, message):
        action, transaction_id = struct.unpack(">LL", message[0:8])
        if action == CONNECT and self.transaction_id == transaction_id:
            self.connect_response(message[8:])
            self.scrape_request()
        elif action == SCRAPE and self.transaction_id == transaction_id:
            self.scrape_response(message[8:])
            if self.need_connect():
                self.connect_request()
            else:
                self.scrape_request()
        elif action == ERROR:
            print('handle_receive error message', message[8:])


class Scraper:
    def __init__(self, clients: Dict[str, TrackerInfo], loop):
        self.clients = clients
        self.loop = loop
        self.transport = None

        self.trackers = {}

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.trackers[addr[0]].handle_receive(data)

    def error_received(self, exc: OSError):
        print(exc)

    def connection_lost(self, exc: OSError):
        print(exc)

    async def scrape(self, queue: asyncio.Queue, batch_size=5000):
        while True:
            infohashes = []
            while len(infohashes) < batch_size:
                item = await queue.get()
                if item is None:
                    break
                infohashes.append(item)

            self.trackers = {ip: TrackerClient(info, self.transport, infohashes, self.loop) for ip, info in self.clients.items() }

            while sum(tracker.finished for tracker in self.trackers.values()) < len(self.trackers):
                await asyncio.sleep(2)

            results = []
            for cols in itertools.zip_longest(*[tracker.results for tracker in self.trackers.values()]):
                cols = [col for col in cols if col is not None]
                if len(cols) > 0:
                    results.append(max(cols, key=lambda c: c[1]))

            await database.update_status(results)

            if len(infohashes) < batch_size:
                break

    async def run(self, database: Torrent, port=8818):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        transport, _ = await self.loop.create_datagram_endpoint(
            lambda: self, sock=s
        )

        queue = asyncio.Queue(maxsize=50000)
        await asyncio.gather(database.fetch_infohash(queue), self.scrape(queue))

        self.transport.close()


def get_clients():
    best_trackers = 'https://github.com/ngosang/trackerslist/raw/master/trackers_best.txt'

    for _ in range(10):
        res = requests.get(best_trackers)
        if res.status_code != 200:
            continue

        trackers = {}
        for url in res.text.split():
            if url.startswith('udp'):
                host, port = url[6:-9].split(':')
                ip = socket.gethostbyname(host)
                trackers[ip] = TrackerInfo(host, ip, int(port))

        return trackers
    else:
        print('''can't get tracker list''')
        raise RuntimeError()


if __name__ == '__main__':
    trackers = get_clients()
    loop = asyncio.get_event_loop()
    database = Torrent()
    scraper = Scraper(trackers, loop)
    while True:
        loop.run_until_complete(scraper.run(database, 8818))