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

f = open(str(int(time.time()))+".ih.log", 'w')

def log(metainfo, infohash):
    if metainfo not in [False, None]:
        try:
            out = infohash+' '+ metainfo[b'name'].decode('utf-8')+'\n'
            sys.stdout.write(out)
            f.write(out)
            f.flush()
        except UnicodeDecodeError:
            print(infohash+'    (not rendered)')

class Mana(Maga):
    def __init__(self, active_tcp_limit = 1000, max_per_session = 2500):
        super().__init__()
        self.seen = []
        self.seen_ct = 0
        self.active = 0
        self.threshold = active_tcp_limit
        self.max = max_per_session
    async def handler(self, infohash, addr, peer_addr = None):
        if self.running and (self.active < self.threshold) and (self.seen_ct < self.max) and (infohash not in self.seen):
            self.seen.append(infohash)
            self.seen_ct += 1
            if peer_addr is None:
                peer_addr = addr
            self.active += 1
            metainfo = await get_metadata(
                infohash, peer_addr[0], peer_addr[1], loop=self.loop
            )
            self.active -= 1
            log(metainfo, infohash)
        #print(self.active, self.seen_ct)
        if (self.seen_ct >= self.max) and (self.active < 100):
            self.stop()
    async def handle_announce_peer(self, infohash, addr, peer_addr):
        await self.handler(infohash, addr, peer_addr)

mana = Mana()
mana.run(6881, False)

if len(sys.argv) > 1 and sys.argv[1] == "--forever":
    while True:
        new_mana = Mana()
        new_mana.seen = mana.seen
        del mana
        mana = new_mana
        new_mana.run(6881, False)
        print('>>> mana round done')
        time.sleep(5)
