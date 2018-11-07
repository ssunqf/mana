import mala, maga
import sys

import asyncio

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

import time

import handlebars

f = open("ih.log", 'a')

class Crawler(maga.Maga):
    def __init__(self, loop=None, active_tcp_limit = 20, max_per_session = 500):
        super().__init__(loop)
        self.seen_ct = 0
        self.active = asyncio.Semaphore(active_tcp_limit)
        self.threshold = active_tcp_limit
        self.max = max_per_session
        self.connection = asyncio.get_event_loop().run_until_complete(handlebars.init_redis('mana.sock'))
        self.backlog = 0

    async def handler(self, infohash, addr, peer_addr = None, reason = None):
        ih_bytes = bytes.fromhex(infohash)
        start_time = int(time.time()*1000)
        try_for_metadata = False
        added_timestamp = await self.connection.hget('infohash_ingress_timestamp', ih_bytes)
        attempted_timestamp = int(await self.connection.hget('infohash_attempt_timestamp', ih_bytes) or b'0')
        peer_addr = peer_addr or addr
        if self.running and self.backlog < 10 and not added_timestamp and (start_time - attempted_timestamp) > 600:
            await self.connection.hincrby('infohash_attempt_reason', reason, 1)
            self.connection.hset('infohash_attempt_timestamp', ih_bytes, start_time)
            print(f'{reason} {addr} {infohash} {self.backlog}')
            self.backlog += 1
            async with self.active:
                self.backlog -= 1
                try:
                    client = mala.WirePeerClient(infohash)
                    await asyncio.wait_for(client.connect(peer_addr[0], peer_addr[1], self.loop), timeout=1)
                    metainfo = await client.work()
                    if metainfo:
                        await self.log(metainfo, infohash, peer_addr, reason)
                        await self.connection.hset('infohash_ingress_timestamp', ih_bytes, start_time)
                        await self.connection.hincrby('infohash_ingress_reason', reason, 1)
                        print('ingress', await self.connection.hgetall('infohash_ingress_reason'))
                        print('attempt', await self.connection.hgetall('infohash_attempt_reason'))
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


port = int(sys.argv[1])

handlebars.start_redis_server('mana.sock')
time.sleep(1)
crawler = Crawler()
crawler.run(port, False)

if len(sys.argv) > 2 and sys.argv[2] == "--forever":
    while True:
        new_crawler = Crawler()
        new_crawler.seen = crawler.seen
        del crawler
        crawler = new_crawler
        time.sleep(5)
        new_crawler.run(port, False)
        print('>>> crawler round done', crawler.loop, new_crawler.loop)
