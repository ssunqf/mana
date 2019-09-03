#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
import json
import logging
from typing import List, Tuple, Dict
from datetime import datetime
from tqdm import tqdm
from parser.nsfw import detect_nsfw

import asyncpg

from util.categories import guess_metainfo
from parser.search import make_tsvector, make_tsquery

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass


class Torrent:
    def __init__(self, host='localhost', loop=None):
        self.loop = loop if loop else asyncio.get_event_loop()

        self.pool = self.loop.run_until_complete(
            asyncpg.create_pool(database='btsearch',
                                host=host,
                                user='sunqf',
                                password='840422',
                                loop=self.loop))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pool.colse()

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
                    seeders INT,
                    completed INT,
                    leechers INT)
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
                        INSERT INTO torrent (infohash, metainfo, category, keyword_ts, adult)
                        VALUES ($1, $2, $3, $4::tsvector, $5)
                        ''',
                        [(infohash.upper(), metainfo, guess_metainfo(metainfo), make_tsvector(metainfo), detect_nsfw(metainfo))
                         for infohash, metainfo in data])
        except Exception as e:
            logging.warning(str(e))

    async def update_status(self, data: List[(Tuple[str, int, int, int])], update_time=datetime.utcnow()):
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.executemany(
                        '''
                        UPDATE torrent
                        SET seeders=$2, completed=$3, leechers=$4, update_time=$5
                        WHERE infohash = $1
                        ''',
                        [(infohash.upper(), seeders, completed, leechers, update_time)
                         for infohash, seeders, completed, leechers, in data]
                    )
        except Exception as e:
            logging.warning(str(e))

    async def fetch_infohash(self, queue: asyncio.Queue):
        limit = 1000
        offset = 0
        while True:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    batch = [row['infohash'] for row in await conn.fetch(
                        f'''
                        SELECT infohash FROM torrent
                        ORDER BY infohash
                        LIMIT {limit} OFFSET {offset}
                        ''')]

            for infohash in batch:
                await queue.put(infohash)

            offset += len(batch)

            if len(batch) < limit:
                await queue.put(None)
                break

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

    async def batch(self, offset, limit):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.set_type_codec(
                    'jsonb',
                    encoder=lambda d: json.dumps(d, ensure_ascii=False),
                    decoder=json.loads,
                    schema='pg_catalog'
                )
                return await conn.fetch(f'''
                    SELECT infohash, metainfo FROM torrent OFFSET {offset} LIMIT {limit}
                ''')

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
                    '''
                    SELECT infohash, metainfo, category, seeders, completed, leechers, update_time
                    FROM torrent
                    WHERE infohash = $1
                    ''',
                    infohash.upper()))

    async def search(self, query, offset=0, limit=20, **kwargs):
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
                    SELECT *, COUNT(*) OVER() AS total
                    FROM (
                        SELECT *, keyword_ts <=> \'%s\'::tsquery AS rank
                        FROM torrent
                        WHERE keyword_ts @@ \'%s\'::tsquery %s
                        ORDER BY keyword_ts <=> \'%s\'::tsquery
                        LIMIT 1000
                    ) AS matched
                    ORDER BY rank, seeders DESC
                    LIMIT %d OFFSET %d
                    ''' % (query, query, 'and ' + conditions if len(kwargs) > 0 else '', query, limit, offset)
                return [dict(row) for row in await conn.fetch(cmd)]

    async def update(self):
        tq = tqdm(desc='update')
        while True:
            try:
                async with self.pool.acquire() as reader:
                    async with reader.transaction():
                        await reader.set_type_codec(
                            'jsonb',
                            encoder=lambda d: json.dumps(d, ensure_ascii=False),
                            decoder=json.loads,
                            schema='pg_catalog'
                        )

                        cmd = f'''
                                SELECT infohash, metainfo FROM torrent
                                ORDER BY infohash
                                LIMIT 200 OFFSET {tq.n}
                            '''
                        buffer = [(row['infohash'], make_tsvector(row['metainfo']), detect_nsfw(row['metainfo'])) for row in await reader.fetch(cmd)]

                if len(buffer) == 0:
                    break

                async with self.pool.acquire() as writer:
                    async with writer.transaction():
                        await writer.executemany(
                            '''UPDATE torrent SET keyword_ts=$2, adult=$3 WHERE infohash = $1''',
                            buffer)

                tq.update(len(buffer))
            except Exception as e:
                raise e

    async def fetch(self, queue: asyncio.Queue, batch_size=300):
        count = 0
        total_time, total = 0., 0
        while True:
            try:
                async with self.pool.acquire() as reader:
                    async with reader.transaction():
                        await reader.set_type_codec(
                            'jsonb',
                            encoder=lambda d: json.dumps(d, ensure_ascii=False),
                            decoder=json.loads,
                            schema='pg_catalog'
                        )

                        cmd = f'''
                            SELECT infohash, metainfo FROM torrent
                            ORDER BY infohash
                            LIMIT {batch_size} OFFSET {count}
                            '''
                        import time
                        start = time.time()
                        batch = await reader.fetch(cmd)
                        total_time += time.time() - start
                        total += 1
                        print('speed: %f' % (total_time * batch_size/total))
                        for row in batch:
                            count += 1
                            await queue.put(row)

                        if len(batch) < batch_size:
                            await queue.put(None)
                            break
            except Exception as e:
                raise e

    async def consumer(self, readq: asyncio.Queue, writeq: asyncio.Queue):
        tq = tqdm(desc='process')
        while True:
            item = await readq.get()
            if item is None:
                await writeq.put(None)
                break
            await writeq.put((item['infohash'], make_tsvector(item['metainfo']), detect_nsfw(item['metainfo'])))
            tq.update()

    async def output(self, writeq: asyncio.Queue, batch_size=500):
        while True:
            batch = []
            while len(batch) < batch_size:
                last = await writeq.get()
                if last is None:
                    break
                batch.append(last)

            if True:
                async with self.pool.acquire() as writer:
                    async with writer.transaction():
                        await writer.executemany(
                            '''UPDATE torrent SET keyword_ts=$2, adult=$3 WHERE infohash = $1''',
                            batch)

            if len(batch) < batch_size:
                break

    async def update_all(self):
        readq, writeq = asyncio.Queue(maxsize=50000), asyncio.Queue(maxsize=50000)
        await asyncio.gather(self.fetch(readq), self.consumer(readq, writeq), self.output(writeq))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    db_client = Torrent(host='207.148.124.42', loop=loop)
    loop.run_until_complete(db_client.update_all())



