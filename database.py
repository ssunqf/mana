#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import functools
import asyncio
from aiopg.sa import create_engine
import sqlalchemy as sa

metadata = sa.MetaData()

torrent_table = sa.Table('torrent', metadata,
                         sa.Column('infohash', sa.String(40), primary_key=True),
                         sa.Column('metadata', sa.LargeBinary()),
                         sa.Column('metainfo', sa.JSON))

class Torrent:
    def __init__(self, loop=None):
        self.loop = loop if loop else asyncio.get_event_loop()

        self.engine = self.loop.run_until_complete(create_engine(user='sunqf',
                                 database='btsearch',
                                 host='127.0.0.1',
                                 password='840422'))

    async def create_table(self):
        async with self.engine.acquire() as conn:
            await conn.execute('''CREATE TABLE torrent (
                infohash varchar(40) PRIMARY KEY,
                metadata bytea,
                metainfo JSONB)''')

    async def save_torrent(self, infohash, metadata, metainfo):
        async with self.engine.acquire() as conn:
            await conn.execute(torrent_table.insert().values(
                infohash=infohash, metadata=metadata, metainfo=metainfo))

    async def select_by_infohash(self, infohash):
        async with self.engine.acquire() as conn:
            await conn.execute(torrent_table.select(infohash=infohash))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    db = Torrent()
    loop.run_until_complete(db.create_table())



