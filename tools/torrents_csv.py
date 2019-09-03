#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
import json
import sys
import re
from util.database import Torrent

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass


def split(line, maxsplit):
    infohash, items = line.split(';', maxsplit=1)
    items = items.split(';', maxsplit=maxsplit)
    return infohash, items


file_pattern = r'^([0-9a-f]{40});(\d*);(.*);(\d*)$'

def load_files(path: str):
    with open(path) as input:
        input.readline()

        infohash, files = None, None
        for line in input:
            matcher = re.fullmatch(file_pattern, line.strip())
            if not matcher:
                continue

            _infohash, _index, _file, _length = matcher.groups()
            if infohash != _infohash:
                if infohash:
                    yield infohash, [f[1] for f in sorted(files, key=lambda f: f[0])]
                files = []
            infohash = _infohash
            files.append((_index, {'path': _file, 'length': int(_length)}))

        if infohash:
            yield infohash, [f[1] for f in sorted(files, key=lambda f: f[0])]


torrent_pattern = r'^([0-9a-f]{40});(.*);(\d*);(-?\d*);(\d*);(\d*);(\d*);(\d*)$'
def load_torrent(path: str):
    with open(path) as input:
        input.readline()

        for line in input:
            matcher = re.fullmatch(torrent_pattern, line.strip())
            if not matcher:
                print('not match', line)
                continue

            _infohash, _name, _size_bytes, _created_unix, _seeders, _leechers, _completed, _scraped_date = matcher.groups()

            yield _infohash, _name, _size_bytes, _seeders, _leechers, _completed


def load():
    # 处理https://gitlab.com/dessalines/torrents.csv获取的数据
    files = iter(load_files('/Users/sunqf/Downloads/torrent_files.csv'))
    curr = None
    for infohash, name, length, seeders, leechers, completed in load_torrent('/Users/sunqf/Downloads/torrents.csv'):
        while curr is None or curr[0] < infohash:
            curr = next(files)

        if curr[0] == infohash:
            yield infohash, {'name': name, 'length': int(length), 'files': curr[1]}
        else:
            yield infohash, {'name': name, 'length': int(length)}


async def upload(torrent, exists, output):
    with open(output, 'w') as writer:
        for infohash, metainfo in tqdm(load()):
            infohash = infohash.upper()
            if infohash not in exists:
                writer.write(json.dumps(
                    {'infohash': infohash, 'metainfo': metainfo},
                    ensure_ascii=False) + '\n')
                # await torrent.save_torrent([(infohash, metainfo)])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    from tqdm import tqdm
    torrent = Torrent('207.148.124.42', loop=loop)
    exists = [] # loop.run_until_complete(torrent.fetch_infohash(limit=-1))
    print('exists', len(exists))
    loop.run_until_complete(upload(torrent, set(exists), sys.argv[1]))