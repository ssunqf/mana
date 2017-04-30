from maga import Maga
from mala import get_metadata
import sys

import asyncio
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

import time

import asyncio_redis

f = open("/root/"+str(int(time.time()))+".ih.log", 'w')

class Crawler(Maga):
    def __init__(self, loop=None, active_tcp_limit = 1000, max_per_session = 2500):
        super().__init__(loop)
        self.seen_ct = 0
        self.active = 0
        self.threshold = active_tcp_limit
        self.max = max_per_session
        asyncio.get_event_loop().run_until_complete(self.connect_redis())

    async def connect_redis(self):
        self.connection = await asyncio_redis.Connection.create('localhost', 6379)

    async def handler(self, infohash, addr, peer_addr = None):
        exists = await self.connection.hexists('hashes', infohash)
        if self.running and (self.active < self.threshold) and (self.seen_ct < self.max) and not exists:
            await self.connection.hset('hashes', infohash, '')
            self.seen_ct += 1
            if peer_addr is None:
                peer_addr = addr
            self.active += 1
            metainfo = await get_metadata(
                infohash, peer_addr[0], peer_addr[1], loop=self.loop
            )
            self.active -= 1
            await self.log(metainfo, infohash)
        if (self.seen_ct >= self.max):
            self.stop()

    async def log(self, metainfo, infohash):
        if metainfo not in [False, None]:
            try:
                out = infohash+' '+ metainfo[b'name'].decode('utf-8')+'\n'
                sys.stdout.write(out)
                f.write(out)
                f.flush()
            except UnicodeDecodeError:
                print(infohash+'    (not rendered)')


    async def handle_announce_peer(self, infohash, addr, peer_addr):
        await self.handler(infohash, addr, peer_addr)

port = int(sys.argv[1])

crawler = Crawler()
crawler.run(port, False)

if len(sys.argv) > 1 and sys.argv[2] == "--forever":
    while True:
        new_crawler = Crawler()
        new_crawler.seen = crawler.seen
        del crawler
        crawler = new_crawler
        time.sleep(5)
        new_crawler.run(port, False)
        print('>>> crawler round done', crawler.loop, new_crawler.loop)
