from maga import Maga
from mala import get_metadata
import sys

import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

def log(metainfo, infohash):
    if metainfo not in [False, None]:
        sys.stdout.write(infohash+' '+ metainfo[b'name'].decode('utf-8')+'\n')
        sys.stdout.flush()
    else:
        sys.stderr.write('saw: '+infohash+'\n')
        sys.stderr.flush()
        

class Crawler(Maga):
    def __init__(self):
        super().__init__()
        self.seen = []
    async def handler(self, infohash, addr, peer_addr = None):
        if infohash not in self.seen:
            self.seen.append(infohash)
            if peer_addr is None:
                peer_addr = addr
            metainfo = await get_metadata(
                infohash, peer_addr[0], peer_addr[1], loop=self.loop
            )
            log(metainfo, infohash)

    async def handle_announce_peer(self, infohash, addr, peer_addr):
        await self.handler(infohash, addr, peer_addr)


crawler = Crawler()
crawler.run(port=10001)
