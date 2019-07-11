#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
import json
import logging
from typing import List, Tuple, Dict

import asyncpg


class Torrent:
    def __init__(self, loop=None):
        self.loop = loop if loop else asyncio.get_event_loop()

        self.pool = self.loop.run_until_complete(
            asyncpg.create_pool(database='postgres',
                                host='localhost',
                                user='sunqf',
                                password='840422'))

    async def create_table(self):
        async with self.pool.acquire() as conn:
            # await conn.execute('''DROP TABLE torrent''')
            await conn.execute('''CREATE TABLE torrent (
                infohash varchar(40) PRIMARY KEY,
                metadata bytea,
                metainfo JSONB)''')

    async def save_torrent(self, data: List[Tuple[str, bytes, Dict]]):
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    conn.executemany(
                        '''INSERT INTO torrent(infohash, metadata, metainfo) VALUES ($1, $2, $3)''',
                        data)
        except Exception as e:
            logging.warning(str(e))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    db = Torrent()
    print(loop.run_until_complete(db.select_infohashs())[0:10])



