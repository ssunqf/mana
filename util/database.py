#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
import json
import logging
from typing import List, Tuple, Dict

import asyncpg

from util.categories import guess_metainfo
from parser.search import make_tsvector, make_tsquery


class Torrent:
    def __init__(self, host='localhost', loop=None):
        self.loop = loop if loop else asyncio.get_event_loop()

        self.pool = self.loop.run_until_complete(
            asyncpg.create_pool(database='btsearch',
                                host=host,
                                user='sunqf',
                                password='840422'))

    async def create_table(self):
        async with self.pool.acquire() as conn:
            # await conn.execute('''DROP TABLE torrent''')
            await conn.execute(
                '''
                CREATE TABLE torrent (
                    infohash varchar(40) PRIMARY KEY,
                    metainfo JSONB,
                    category TEXT,
                    keyword_ts TSVECTOR,
                    complete INT,
                    downloaded INT,
                    incomplete INT)
                ''')

    async def save_torrent(self, data: List[Tuple[str, Dict]]):
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.set_type_codec(
                        'jsonb',
                        encoder=lambda d: json.dumps(d, ensure_ascii=False),
                        decoder=json.loads,
                        schema='pg_catalog'
                    )
                    await conn.executemany(
                        '''
                        INSERT INTO torrent (infohash, metainfo, category, keyword_ts)
                        VALUES ($1, $2, $3, $4::tsvector)
                        ''',
                        [(infohash, metainfo, guess_metainfo(metainfo), make_tsvector(metainfo))
                         for infohash, metainfo in data])
        except Exception as e:
            logging.warning(str(e))

    async def update_status(self, data: List[(Tuple[str, int, int, int])]):
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(
                        '''
                        UPDATE torrent
                        SET complete=$2, downloaded=$3, incomplete=$4, update_time=current_timestamp
                        WHERE infohash = $1
                        ''',
                        data
                    )
        except Exception as e:
            logging.warning(str(e))

    async def get_all(self):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                return [row['infohash'] for row in await conn.fetch('''SELECT infohash FROM torrent''')]

    async def foreach(self, table_name, column_name, alias_name):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.set_type_codec(
                    'jsonb',
                    encoder=lambda d: json.dumps(d, ensure_ascii=False),
                    decoder=json.loads,
                    schema='pg_catalog'
                )
                return [row[alias_name] async for row in conn.fetch(
                    '''SELECT %s as %s FROM %s''' % (column_name, alias_name, table_name))]

    async def get_by_infohash(self, infohash):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.set_type_codec(
                    'jsonb',
                    encoder=lambda d: json.dumps(d, ensure_ascii=False),
                    decoder=json.loads,
                    schema='pg_catalog'
                )
                return dict(await conn.fetchrow(
                    '''SELECT infohash, metainfo, category FROM torrent WHERE infohash = $1''',
                    infohash))

    async def search(self, query, **kwargs):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.set_type_codec(
                    'jsonb',
                    encoder=lambda d: json.dumps(d, ensure_ascii=False),
                    decoder=json.loads,
                    schema='pg_catalog'
                )

                query = make_tsquery(query)
                conditions = ' and '.join([('%s=%d' if isinstance(v, int) else'%s=\'%s\'') % (k, v)
                                           for k, v in kwargs.items()])

                cmd = '''
                    SELECT infohash, metainfo, category
                    FROM torrent
                    WHERE keyword_ts @@ \'%s\'::tsquery %s
                    ORDER BY keyword_ts <=> \'%s\'::tsquery
                    ''' % (query, 'and ' + conditions if len(kwargs) > 0 else '', query)
                return [dict(row) for row in await conn.fetch(cmd)]


db_client = Torrent()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(db_client.set_category())



