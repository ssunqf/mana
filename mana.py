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


f = open("ih.log", 'a')


class Crawler(maga.Maga):
    def __init__(self, loop=None, active_tcp_limit = 20, max_per_session = 500):
        super().__init__(loop)
        self.seen_ct = 0
        self.active = asyncio.Semaphore(active_tcp_limit)
        self.threshold = active_tcp_limit
        self.max = max_per_session
        self.redis_client = asyncio.get_event_loop().run_until_complete(
                aioredis.create_redis_pool('redis://localhost'))
        self.backlog = 0

    async def handler(self, infohash, addr, peer_addr = None, reason = None):
        ih_bytes = bytes.fromhex(infohash)
        start_time = int(time.time()*1000)
        try_for_metadata = False
        added_timestamp = await self.redis_client.hget('infohash_ingress_timestamp', ih_bytes)
        attempted_timestamp = int(await self.redis_client.hget('infohash_attempt_timestamp', ih_bytes) or b'0')
        peer_addr = peer_addr or addr
        if self.running and self.backlog < 10 and not added_timestamp and (start_time - attempted_timestamp) > 600:
            await self.redis_client.hincrby('infohash_attempt_reason', reason, 1)
            self.redis_client.hset('infohash_attempt_timestamp', ih_bytes, start_time)
            print(f'{reason} {addr} {infohash} {self.backlog}')
            self.backlog += 1
            async with self.active:
                self.backlog -= 1
                try:
                    metainfo = await self.fetch_from_url(infohash)
                    if metainfo is None:
                        client = mala.WirePeerClient(infohash)
                        await asyncio.wait_for(client.connect(peer_addr[0], peer_addr[1], self.loop), timeout=1)
                        metainfo = await client.work()

                    if metainfo:
                        await self.log(metainfo, infohash, peer_addr, reason)
                        await self.redis_client.hset('infohash_ingress_timestamp', ih_bytes, start_time)
                        await self.redis_client.hincrby('infohash_ingress_reason', reason, 1)
                        print('ingress', await self.redis_client.hgetall('infohash_ingress_reason'))
                        print('attempt', await self.redis_client.hgetall('infohash_attempt_reason'))
                except (ConnectionRefusedError, ConnectionResetError, asyncio.streams.IncompleteReadError, asyncio.TimeoutError, OSError) as e:
                    if isinstance(e, OSError) and e.errno not in (101, 104, 111,113):
                        raise
                    pass
        if (self.seen_ct >= self.max):
            self.stop()

    async def log(self, metainfo, infohash, peer_addr, reason):
        if metainfo not in [False, None]:
            self.seen_ct += 1
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

    async def fetch_from_url(self, infohash):
        url = f'http://thetorrent.org/{infohash}.torrent'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                print(response.content_type)
                if response.content_type == 'application/x-bittorrent':
                    torrent_file = await response.text()
                    print(torrent_file)
                    return better_bencode.loads(torrent_file)
                else:
                    return None


INFOHASH_FOUND = 'INFOHASH_FOUND'
INFOHASH_UNFOUND = 'INFOHASH_UNFOUND'

class InfoHashCrawler(maga.Maga):
    def __init__(self, redis_address=None):
        self.redis_client = asyncio.get_event_loop().run_until_complete(
            aioredis.create_redis_pool('redis://localhost' if redis_address == None else redis_address))

        self.get_peers_count = 0
        self.announce_peer_count = 0

    async def handler(self, infohash, addr, peer_addr = None, reason = None):
        if reason == 'get_peers':
            self.get_peers_count += 1
        elif reason == 'announce_peer':
            self.announce_peer_count += 1

        if self.get_peers_count % 1000 == 0:
            print(f'get_peers: {self.get_peers_count}\tannounce_peer: {self.announce_peer_count}')

        if (await self.redis_client.sismember(INFOHASH_FOUND, infohash)) == 0:
            peer_addr = peer_addr or addr
            await self.redis_client.zadd(INFOHASH_UNFOUND,
                                         int(time.time() * 1000),
                                         f'{infohash}:{peer_addr[0]}:{peer_addr[1]}')


class InfoHashFecther:
    def __init__(self, redis_address=None, timeout=6000, active_tcp_limit=200):
        self.redis_client = asyncio.get_event_loop().run_until_complete(
            aioredis.create_redis_pool('redis://localhost' if redis_address == None else redis_address))

        self.tcp_limit = asyncio.Semaphore(active_tcp_limit)
        self.timeout = timeout

    async def run(self):
        while True:
            results = await self.redis_client.zrange(INFOHASH_UNFOUND, 0, 5, withscores=True)
            self.redis_client.zremrangebyrank(INFOHASH_UNFOUND, 0, len(results)/2)
            assert len(results) % 2 == 0
            for offset in range(0, len(results), 2):
                infohash, timestamp = results[offset:offset+2]
                if time.time() - timestamp > self.timeout:
                    continue
                infohash, ip, address = infohash.split(':')

                async with self.tcp_limit:
                    async with mala.WirePeerClient(infohash, ip, address, self.loop) as client:
                        metainfo = client.work()
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

fetcher = InfoHashFecther()
asyncio.get_event_loop().create_task(fetcher.run)

time.sleep(1)
crawler = InfoHashCrawler()
crawler.run(port, False)

if len(sys.argv) > 2 and sys.argv[2] == "--forever":
    while True:
        new_crawler = InfoHashCrawler()
        new_crawler.seen = crawler.seen
        del crawler
        crawler = new_crawler
        time.sleep(5)
        new_crawler.run(port, False)
        print('>>> crawler round done', crawler.loop, new_crawler.loop)
