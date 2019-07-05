import mala, maga
import sys

import asyncio
import aioredis
import aiohttp
import itertools

import better_bencode

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

import time

INFOHASH_FOUND = 'INFOHASH_FOUND'
INFOHASH_LAST_STAMP = 'INFOHASH_LAST_STAMP'

f = open("ih.log", 'a')


class Crawler(maga.Maga):
    def __init__(self, loop=None, active_tcp_limit = 200, max_per_session = 500):
        super().__init__(loop)
        self.seen_ct = 0
        self.active_tcp_limit = asyncio.Semaphore(active_tcp_limit)
        self.threshold = active_tcp_limit
        self.max = max_per_session
        self.redis_client = asyncio.get_event_loop().run_until_complete(
                aioredis.create_redis_pool('redis://localhost'))

    async def handler(self, infohash, addr, peer_addr = None, reason = None):
        ih_bytes = bytes.fromhex(infohash)
        start_time = int(time.time()*1000)

        if await self.redis_client.sismember(INFOHASH_FOUND, ih_bytes):
            return

        last_stamp = await self.redis_client.hget(INFOHASH_LAST_STAMP, ih_bytes)
        if self.running and last_stamp and start_time - last_stamp > 600:
            peer_addr = peer_addr or addr
            print(f'{reason} {addr} {infohash}')
            async with self.active_tcp_limit:
                try:
                    metainfo = await mala.get_metadata(infohash, peer_addr[0], peer_addr[1], self.loop)
                    if metainfo:
                        await self.log(metainfo, infohash, peer_addr, reason)
                        await self.redis_client.sadd(INFOHASH_FOUND, ih_bytes)
                        await self.redis_client.hdel(INFOHASH_LAST_STAMP, ih_bytes)
                    else:
                        await self.redis_client.hset(INFOHASH_LAST_STAMP, ih_bytes, start_time)
                except (ConnectionRefusedError, ConnectionResetError, asyncio.streams.IncompleteReadError, asyncio.TimeoutError, OSError) as e:
                    if isinstance(e, OSError) and e.errno not in (101, 104, 111,113):
                        raise
                    pass
                    await self.redis_client.hset(INFOHASH_LAST_STAMP, ih_bytes, start_time)

    async def log(self, metainfo, infohash, peer_addr, reason):
        if metainfo not in [False, None]:
            try:
                sanitized_name = metainfo[b"name"].decode().replace('\n', '|')
                out = f'{infohash} {sanitized_name}\n'
                sys.stdout.write(f'{peer_addr} {reason} {out}')
                if metainfo.get(b'files'):
                    filepaths = [(b'/'.join(x.get(b'path.utf-8') or x.get(b'path'))).decode() for x in metainfo[b'files']]
                    print(filepaths)
                f.write(out)
                f.flush()
            except UnicodeDecodeError:
                print(infohash+'    (not rendered)')


class InfoHashCrawler(maga.Maga):
    def __init__(self, redis_address=None, loop=None, active_tcp_limit = 20, max_per_session = 500):
        super(InfoHashCrawler, self).__init__(loop)
        self.redis_client = asyncio.get_event_loop().run_until_complete(
            aioredis.create_redis_pool('redis://localhost' if redis_address == None else redis_address))

        self.get_peers_count = 0
        self.announce_peer_count = 0

    async def handler(self, infohash, addr, peer_addr = None, reason = None):
        if reason == 'get_peer':
            self.get_peers_count += 1
        elif reason == 'announce_peer':
            self.announce_peer_count += 1

        if self.get_peers_count % 1000 == 0:
            print(f'get_peer: {self.get_peers_count}\tannounce_peer: {self.announce_peer_count}')
            found_count = await self.redis_client.scard(INFOHASH_FOUND)
            unfound_count = await self.redis_client.zcard(INFOHASH_UNFOUND)
            print(f'found: {found_count}\tunfound:{unfound_count}')

        if (await self.redis_client.sismember(INFOHASH_FOUND, infohash)) == 0:
            peer_addr = peer_addr or addr
            await self.redis_client.zadd(INFOHASH_UNFOUND,
                                         int(time.time()),
                                         f'{infohash}:{peer_addr[0]}:{peer_addr[1]}')


class InfoHashFecther:
    def __init__(self, loop, redis_address=None, timeout=1, active_tcp_limit=200):
        self.loop = loop
        self.redis_client = self.loop.run_until_complete(
            aioredis.create_redis_pool('redis://localhost' if redis_address == None else redis_address))

        self.tcp_limit = asyncio.Semaphore(active_tcp_limit)
        self.timeout = timeout

    async def run(self):
        while True:
            results = await self.redis_client.zrange(INFOHASH_UNFOUND, 0, 5, withscores=True)
            if len(results) == 0:
                asyncio.sleep(0.5)
                continue
            else:
                await self.redis_client.zremrangebyrank(INFOHASH_UNFOUND, 0, 5)

            async for infohash, timestamp in results:
                if time.time() - timestamp > self.timeout:
                    continue
                infohash, ip, address = infohash.split(b':')

                async with self.tcp_limit:
                    metainfo = await mala.get_metadata(infohash, ip, address, self.loop)
                    print(infohash, metainfo)
                    if metainfo:
                        await self.save(infohash, metainfo)
                        await self.redis_client.sadd(INFOHASH_FOUND, infohash)

    async def save(self, infohash, metainfo):
        if metainfo not in [False, None]:
            try:
                sanitized_name = metainfo[b"name"].decode().replace('\n', '|')
                out = f'{infohash} {sanitized_name}\n'

                if metainfo.get(b'files'):
                    filepaths = [(b'/'.join(x.get(b'path.utf-8') or x.get(b'path'))).decode() for x in metainfo[b'files']]
                    print(filepaths)
                print(out)
            except UnicodeDecodeError:
                print(infohash+'    (not rendered)')


port = int(sys.argv[1])

loop = asyncio.get_event_loop()
fetcher = InfoHashFecther(loop)
asyncio.create_task(fetcher.run(), loop=loop)

time.sleep(1)
crawler = InfoHashCrawler()
crawler.run(port, False)

loop.run_forever()
