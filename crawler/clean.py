#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import sys
import asyncio
import aioredis
from tqdm import tqdm


loop = asyncio.get_event_loop()
redis_client = loop.run_until_complete(
    aioredis.create_redis_pool('redis://localhost'))

INFOHASH_FOUND = 'INFOHASH_FOUND'


async def remove(path):
    with open(path) as input:
        curr = None
        num_peers = 0
        for line in tqdm(input):
            next, *values = line.split()
            values = map(int, values)
            if curr is None:
                curr = next
                num_peers = sum(values)
            elif curr == next:
                num_peers = max(num_peers, sum(values))
            else:
                if not await redis_client.sismember(INFOHASH_FOUND, bytes.fromhex(curr)):
                    print('%s\t%d' % (curr, num_peers))

                curr = next
                num_peers = sum(values)


if __name__ == '__main__':
    loop.run_until_complete(remove(sys.argv[1]))