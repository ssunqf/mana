#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import aioredis
import asyncio
from util.database import Torrent
from tqdm import tqdm

INFOHASH_FOUND = 'INFOHASH_FOUND'
INFOHASH_COUNTER = 'INFOHASH_COUNTER'
INFOHASH_LAST_STAMP = 'INFOHASH_LAST_STAMP'
PEER_STAT = 'PEER_STAT'


class Cache:
    def __init__(self, loop=None):
        self.loop = loop if loop else asyncio.get_running_loop()
        self.redis_client = self.loop.run_until_complete(
                aioredis.create_redis_pool('redis://localhost'))

    async def cache_infohash(self, infohash):
        return await self.redis_client.sadd(INFOHASH_FOUND, bytes.fromhex(infohash))

    async def find_infohash(self, infohash):
        return await self.redis_client.sismember(INFOHASH_FOUND, bytes.fromhex(infohash))

    async def warmup_infohash(self, queue: asyncio.Queue):
        tq = tqdm(desc='warmup cache')
        while True:
            infohash = await queue.get()
            if infohash is None:
                break
            await self.cache_infohash(infohash)
            tq.update()

    def warmup(self, database: Torrent):
        queue = asyncio.Queue(maxsize=100000)
        self.loop.run_until_complete(asyncio.gather(
            database.fetch_infohash(queue), self.warmup_infohash(queue)))