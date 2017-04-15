from maga import Maga
from mala import get_metadata
import sys

import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

import time

f = open("/root/"+str(int(time.time()))+".ih.log", 'w')

def log(metainfo, infohash):
    if metainfo not in [False, None]:
        print(metainfo[b'name'])
        try:
            f.write(infohash+' '+ metainfo[b'name'].decode('utf-8')+'\n')
            f.flush()
        except UnicodeEncodeError:
            print('    (not rendered)')

class Crawler(Maga):
    def __init__(self, active_tcp_limit = 10000):
        super().__init__()
        self.seen = []
        self.active = 0
        self.threshold = active_tcp_limit
    async def handler(self, infohash, addr, peer_addr = None):
        if (self.active < self.threshold) and infohash not in self.seen:
            self.seen.append(infohash)
            if peer_addr is None:
                peer_addr = addr
            self.active += 1
            metainfo = await get_metadata(
                infohash, peer_addr[0], peer_addr[1], loop=self.loop
            )
            self.active -= 1
            log(metainfo, infohash)
            print(self.active)
    async def handle_announce_peer(self, infohash, addr, peer_addr):
        await self.handler(infohash, addr, peer_addr)

crawler = Crawler()
crawler.run()#port=10001)
