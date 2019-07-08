#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import json
import asyncio
from aiopg.sa import create_engine
import sqlalchemy as sa
import psycopg2
import logging

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
            await conn.execute('''DROP TABLE torrent''')
            await conn.execute('''CREATE TABLE torrent (
                infohash varchar(40) PRIMARY KEY,
                metadata bytea,
                metainfo JSONB)''')

    async def save_torrent(self, infohash, metadata, metainfo):
        async with self.engine.acquire() as conn:
            try:
                await conn.execute(torrent_table.insert().values(
                    infohash=infohash,
                    metadata=metadata,
                    metainfo=json.dumps(metainfo, ensure_ascii=False)))
            except psycopg2.errors.UniqueViolation as e:
                logging.warning(str(e))

    async def select_by_infohash(self, infohash):
        async with self.engine.acquire() as conn:
            await conn.execute(torrent_table.select().where(infohash=infohash))

    async def select_infohashs(self):
        async with self.engine.acquire() as conn:
            await conn.execute(torrent_table.select([sa.Column('infohash')]))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    db = Torrent()
    loop.run_until_complete(db.create_table())



