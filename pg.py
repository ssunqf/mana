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

async def _create_table(conn):
    # await conn.execute('DROP TABLE IF EXISTS torrent')
    await conn.execute('''CREATE TABLE torrent (
        infohash varchar(40) PRIMARY KEY,
        metadata bytea,
        metainfo JSONB)''')


async def _save(conn, infohash, metadata, metainfo):
    await conn.execute(torrent_table.insert().values(
        infohash=infohash, metadata=metadata, metainfo=metainfo))


async def _select_by_infohash(conn, infohash):
    await conn.execute(torrent_table.select(infohash=infohash))


async def execute(func, *args, **kwargs):
    async with create_engine(user='xxxx',
                             database='btsearch',
                             host='127.0.0.1',
                             password='xxxx') as engine:
        async with engine.acquire() as conn:
            return await func(conn, *args, **kwargs)

create_table = functools.partial(execute, func=_create_table)
save = functools.partial(execute, func=_save)
select_by_infohash = functools.partial(execute, _select_by_infohash)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(create_table())



