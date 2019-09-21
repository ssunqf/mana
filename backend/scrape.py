import asyncio
import random
import socket
import struct
import time
import itertools
from typing import Dict
from collections import namedtuple
from tqdm import tqdm

import logging
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
        self.results = []

        self.finished = False

        self.connect_request()

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
        self.connection_id = struct.unpack(">Q", message)[0]
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

        batch = self.infohashes[len(self.results):len(self.results)+BATCH_SIZE]
        for infohash, offset in zip(batch, range(0, len(message), 12)):
            seeders, completed, leechers = struct.unpack(">LLL", message[offset:offset+12])
            self.results.append((infohash, seeders, completed, leechers))

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
            logging.error('handle_receive error message', message[8:])


class Scraper:
    def __init__(self, clients: Dict[str, TrackerInfo], loop):
        self.clients = clients
        self.loop = loop
        self.transport = None

        self.trackers = {}
        self.task_queue = asyncio.Queue(maxsize=5000)
        self.update_queue = asyncio.Queue(maxsize=5000)

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.trackers[addr[0]].handle_receive(data)

    def error_received(self, exc: OSError):
        logging.error(exc)

    def connection_lost(self, exc: OSError):
        logging.error(exc)

    async def put(self, infohash):
        await self.task_queue.put(infohash)

    async def fetch(self, database):
        while True:
            await database.fetch_infohash(self.task_queue)

    async def scrape(self, batch_size=BATCH_SIZE * 50):
        tq = tqdm(desc='scrape')
        while True:
            infohashes = []
            while len(infohashes) < batch_size:
                item = await self.task_queue.get()
                if item is None:
                    break
                infohashes.append(item)

            self.trackers = {
                ip: TrackerClient(info, self.transport, infohashes, self.loop) for ip, info in self.clients.items()
            }

            while sum(tracker.finished for tracker in self.trackers.values()) < len(self.trackers):
                await asyncio.sleep(2)

            for cols in itertools.zip_longest(*[tracker.results for tracker in self.trackers.values()]):
                cols = [col for col in cols if col is not None]
                if len(cols) > 0:
                    await self.update_queue.put(max(cols, key=lambda c: c[1]))

            tq.update(len(infohashes))

    async def update(self, database, batch_size=500):
        while True:
            data = []
            while len(data) < batch_size:
                data.append(await self.update_queue.get())
            await database.update_status(data)

    async def run(self, database: Torrent, port=8818):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        transport, _ = await self.loop.create_datagram_endpoint(
            lambda: self, sock=s
        )

        await asyncio.gather(self.fetch(database), self.scrape(), self.update())

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
        logging.error('''can't get tracker list''')
        raise RuntimeError()


if __name__ == '__main__':
    trackers = get_clients()
    loop = asyncio.get_event_loop()
    database = Torrent()
    scraper = Scraper(trackers, loop)
    loop.run_until_complete(scraper.run(database, 8818))