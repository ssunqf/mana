import asyncio
import logging
import sys

import aioredis
from tqdm import tqdm

from util import database
from crawler import dht, peer, cache
from util.torrent import metainfo2json

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

import time

TORRENT_INDEX = 'torrent'

INFOHASH_FOUND = 'INFOHASH_FOUND'
INFOHASH_COUNTER = 'INFOHASH_COUNTER'
INFOHASH_LAST_STAMP = 'INFOHASH_LAST_STAMP'
PEER_STAT = 'PEER_STAT'


class Crawler(dht.DHT):
    def __init__(self, loop=None, active_tcp_limit = 500):
        super().__init__(loop)
        self.active_tcp_limit = asyncio.Semaphore(active_tcp_limit)
        self.threshold = active_tcp_limit

        self.db_client = database.Torrent(loop=self.loop)

        self.cache = cache.Cache(self.loop)

        self.loop.run_until_complete(self.cache.warmup(self.db_client))

        self.get_peer_count = 0
        self.announce_peer_count = 0
        self.exist_count = 0
        self.insert_count = 0
        self.try_metainfo_count = 0
        self.success_metainfo_count = 0
        self.start_time = time.time()

    async def handler(self, infohash, addr, peer_addr = None, reason = None):

        self.get_peer_count += reason == 'get_peers'
        self.announce_peer_count += reason == 'announce_peer'

        logging.debug(f'{reason} {addr} {infohash}')

        assert reason in ['get_peers', 'announce_peer']

        if reason == 'get_peers' or peer_addr is None:
            return

        if await self.cache.find_infohash(infohash):
            self.exist_count += 1
            return

        try:
            async with self.active_tcp_limit:
                self.try_metainfo_count += 1
                metadata = await peer.get_metadata(infohash, peer_addr[0], peer_addr[1])
                self.success_metainfo_count += (metadata is not None)

            metainfo = metainfo2json(metadata)
            if metainfo:
                self.log(infohash, metadata, metainfo)

                await self.db_client.save_torrent([(infohash, metainfo)])
                self.insert_count += 1

                await self.cache.cache_infohash(infohash)

        except (ConnectionRefusedError, ConnectionResetError,
                asyncio.streams.IncompleteReadError, asyncio.TimeoutError, OSError) as e:
            logging.warning(e)
            if isinstance(e, OSError) and e.errno not in (101, 104, 111,113):
                raise

        self.stat()

    def stat(self):
        if (self.get_peer_count + 1) % 10000 == 0:
            duration = time.time() - self.start_time
            logging.warning(f'speed(per second): get_peer={self.get_peer_count / duration}\t'
                  f'announce_peer={self.announce_peer_count / duration}\t'
                  f'exist={self.exist_count / duration}\t'
                  f'try_metainfo={self.try_metainfo_count / duration}\t'
                  f'success_metainfo={self.success_metainfo_count / duration}\t'
                  f'insert={self.insert_count / duration}\t')

            logging.warning(f'fetch metainfo success ratio = {self.success_metainfo_count / self.try_metainfo_count}')

            self.get_peer_count = 0
            self.announce_peer_count = 0
            self.exist_count = 0
            self.insert_count = 0
            self.try_metainfo_count = 0
            self.success_metainfo_count = 0
            self.start_time = time.time()

    def log(self, infohash, metadata, metainfo):
        if metadata not in [False, None]:
            sanitized_name = metainfo["name"]
            logging.debug(f'{infohash} {sanitized_name}')
            if metainfo.get('files'):
                filepaths = [x['path'] for x in metainfo['files']]
                logging.debug(filepaths)


if __name__ == '__main__':

    port = int(sys.argv[1])
    time.sleep(1)

    logger = logging.getLogger()
    logger.setLevel('INFO')

    loop = asyncio.get_event_loop()

    crawler = Crawler(loop)
    # loop.run_until_complete(crawler.warmup())
    loop.run_until_complete(crawler.run(port))



