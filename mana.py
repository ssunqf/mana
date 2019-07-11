import asyncio
import logging
import sys

import aioredis
import aiofiles

import database
import maga
import mala
from torrent import metainfo2json

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

import time

TORRENT_INDEX = 'torrent'

INFOHASH_FOUND = 'INFOHASH_FOUND'
INFOHASH_LAST_STAMP = 'INFOHASH_LAST_STAMP'
PEER_STAT = 'PEER_STAT'


class Crawler(maga.Maga):
    def __init__(self, loop=None, active_tcp_limit = 500):
        super().__init__(loop)
        self.active_tcp_limit = asyncio.Semaphore(active_tcp_limit)
        self.threshold = active_tcp_limit

        self.redis_client = asyncio.get_event_loop().run_until_complete(
                aioredis.create_redis_pool('redis://localhost'))

        self.db_client = database.Torrent(loop)

        self.get_peer_count = 0
        self.announce_peer_count = 0
        self.try_metainfo_count = 0
        self.success_metainfo_count = 0
        self.start_time = time.time()

    async def handler(self, infohash, addr, peer_addr = None, reason = None):

        self.get_peer_count += reason == 'get_peers'
        self.announce_peer_count += reason == 'announce_peer'

        logging.warning(f'{reason} {addr} {infohash}')

        assert reason in ['get_peers', 'announce_peer']
        if reason == 'get_peers' or peer_addr is None:
            return

        if await self.redis_client.sismember(INFOHASH_FOUND, infohash):
            return

        try:
            async with self.active_tcp_limit:
                self.try_metainfo_count += 1
                metadata = await mala.get_metadata(infohash, peer_addr[0], peer_addr[1])
                self.success_metainfo_count += not metadata

            metainfo = metainfo2json(metadata)
            if metainfo:
                self.log(infohash, metadata, metainfo)

                await self.db_client.save_torrent(infohash,
                                                  metadata,
                                                  metainfo)

                await self.redis_client.sadd(INFOHASH_FOUND, infohash)

        except (ConnectionRefusedError, ConnectionResetError,
                asyncio.streams.IncompleteReadError, asyncio.TimeoutError, OSError) as e:
            if isinstance(e, OSError) and e.errno not in (101, 104, 111,113):
                raise

        self.stat()
        if self.get_peer_count == 50000:
            self.running = False

    def stat(self):
        if (self.get_peer_count + 1) % 10000 == 0:
            duration = time.time() - self.start_time
            logging.warning(f'speed(per second): get_peer={self.get_peer_count / duration}\t'
                  f'announce_peer={self.announce_peer_count / duration}\t'
                  f'try_metainfo={self.try_metainfo_count / duration}\t'
                  f'success_metainfo={self.success_metainfo_count / duration}\t')

            logging.warning(f'fetch metainfo success ratio = {self.success_metainfo_count / self.try_metainfo_count}')

            self.get_peer_count = 0
            self.announce_peer_count = 0
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

    while True:
        crawler = Crawler(loop)
        loop.run_until_complete(crawler.run(port, False))



