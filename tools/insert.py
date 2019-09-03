#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
import json
import sys

from util.database import Torrent


async def insert(torrent, path):

    with open(path) as input:
        for line in input:
            info = json.loads(line)

            await torrent.save_torrent([(info['infohash'], info['metainfo'])])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    torrent = Torrent(loop=loop)
    asyncio.get_event_loop().run_until_complete(insert(torrent, sys.argv[1]))