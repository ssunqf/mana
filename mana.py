import mala, maga
import sys

import base64

import asyncio
import aioredis

import database

from torrent import torrent2json

from elasticsearch_async import AsyncElasticsearch

from better_bencode import dumps as bencode, loads as bdecode

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

import time

TORRENT_INDEX = 'torrent'

INFOHASH_FOUND = 'INFOHASH_FOUND'
INFOHASH_LAST_STAMP = 'INFOHASH_LAST_STAMP'

class Crawler(maga.Maga):
    def __init__(self, loop=None, active_tcp_limit = 500):
        super().__init__(loop)
        self.seen_ct = 0
        self.active_tcp_limit = asyncio.Semaphore(active_tcp_limit)
        self.threshold = active_tcp_limit

        self.redis_client = asyncio.get_event_loop().run_until_complete(
                aioredis.create_redis_pool('redis://localhost'))

        self.es_client = AsyncElasticsearch(hosts=['localhost'])

        self.db_client = database.Torrent(loop)

        mapping = '''
            {  
              "mappings": { 
                "properties": {
                  "infohash": {
                    "type": "text"
                  },
                  "metadata": {
                    "type": "binary"
                  },
                  "metainfo":{
                    "type": "nested"
                  }
                }
              }
            }'''
        self.es_client.indices.create(index=TORRENT_INDEX, body=mapping, ignore=400)

        self.get_peer_count = 0
        self.announce_peer_count = 0
        self.try_metainfo_count = 0
        self.success_metainfo_count = 0
        self.stat_time = time.time() * 1000

    async def handler(self, infohash, addr, peer_addr = None, reason = None):
        ih_bytes = bytes.fromhex(infohash)

        self.get_peer_count += reason == 'get_peer'
        self.announce_peer_count += reason == 'announce_peer'

        if await self.redis_client.sismember(INFOHASH_FOUND, ih_bytes):
            return
        # 如果之前失败过，短时间也不会再试
        last_stamp = int(await self.redis_client.hget(INFOHASH_LAST_STAMP, ih_bytes) or b'0')

        start_time = int(time.time()*1000)
        if self.running and start_time - last_stamp > 600:
            peer_addr = peer_addr or addr
            print(f'{reason} {addr} {infohash}')
            async with self.active_tcp_limit:
                try:
                    self.try_metainfo_count += 1
                    metadata = await mala.get_metadata(infohash, peer_addr[0], peer_addr[1], self.loop)
                    if metadata:
                        metainfo = torrent2json(metadata)
                        self.success_metainfo_count += 1
                        await self.save_db(infohash, metadata, metainfo)
                        await self.redis_client.sadd(INFOHASH_FOUND, ih_bytes)
                        await self.redis_client.hdel(INFOHASH_LAST_STAMP, ih_bytes)
                    else:
                        await self.redis_client.hset(INFOHASH_LAST_STAMP, ih_bytes, start_time)
                except (ConnectionRefusedError, ConnectionResetError, asyncio.streams.IncompleteReadError, asyncio.TimeoutError, OSError) as e:
                    if isinstance(e, OSError) and e.errno not in (101, 104, 111,113):
                        raise
                    pass
                    await self.redis_client.hset(INFOHASH_LAST_STAMP, ih_bytes, start_time)

        duration = start_time - self.stat_time
        if self.get_peer_count % 10000 == 0:
            print(f'speed(per second): get_peer={self.get_peer_count * 1000 / duration}\t'
                  f'announce_peer={self.announce_peer_count * 1000 / duration}\t'
                  f'try_metainfo={self.try_metainfo_count * 1000 / duration}\t'
                  f'success_metainfo={self.success_metainfo_count * 1000 / duration}\t')

            print(f'fetch metainfo success ratio = {self.success_metainfo_count / self.try_metainfo_count}')

    async def save_db(self, infohash, metadata, metainfo):
        if metainfo not in [False, None]:
            sanitized_name = metainfo["name"].decode().replace('\n', '|')
            print(f'{infohash} {sanitized_name}')
            if metainfo.get('files'):
                filepaths = [('/'.join(x.get('path.utf-8') or x.get('path'))).decode() for x in metainfo['files']]
                print(filepaths)

            await self.db_client.save_torrent(infohash, metadata, metainfo)


if __name__ == '__main__':

    port = int(sys.argv[1])
    time.sleep(1)
    crawler = Crawler()
    crawler.run(port, False)

