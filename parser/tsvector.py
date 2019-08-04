#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import re
import asyncio
from util.database import Torrent
from parser.parse import parse
from parser.lang import tokenize
from parser.patterns import spam_patterns
import json
from util.categories import guess_metainfo
from tqdm import tqdm


def make_tsvector(metainfo):
    def get_level(ratio):
        levels = [(0.8, 'A'), (0.5, 'B'), (0.3, 'C'), (0, 'D')]
        for thres, level in levels:
            if ratio >= thres:
                return level
        return 'D'

    def is_filter(text):
        return re.search(spam_patterns, text) is not None

    def _each(metainfo):
        yield metainfo['name'], 'A'
        if 'files' in metainfo:
            total_length = sum(file['length'] for file in metainfo['files'])
            for file in sorted(metainfo['files'], key=lambda f: f['length'], reverse=True):
                if not is_filter(file['path']):
                    yield file['path'], get_level(file['length']/total_length)

    vector = {}
    offset = 1
    for file, level in _each(metainfo):
        fields, phrases = parse(file)

        for word in tokenize(file):
            if len(word) > 100:
                print(word)
            if word not in vector:
                vector[word] = ['%d%s' % (offset, level)]
            else:
                vector[word].append('%d%s' % (offset, level))

            offset += 1

        offset += 1

        '''
        for phrase in phrases:
            for id, word in enumerate(tokenize(phrase)):
                if word not in vector:
                    vector[word] = ['%d%s' % (offset, level)]
                else:
                    vector[word].append('%d%s' % (offset, level))

                offset += 1
            # 分割不连续的短语
            offset += 1
        '''

    def to_str(v):
        res = []
        for token, positions in v.items():
            if len(positions) > 200:
                positions = sorted(positions, key=lambda x:x[-1])
            res.append(token + ':' + ','.join(positions[:200]))
        return ' '.join(res)

    return to_str(vector)


async def update_tsvector(torrent):
    async with torrent.pool.acquire() as reader:
        async with torrent.pool.acquire() as writer:
            async with reader.transaction():
                tq = tqdm(desc='update')
                async for row in reader.cursor('SELECT infohash, metainfo FROM torrent ORDER BY infohash'):
                    tq.update(1)
                    infohash = row['infohash']
                    metainfo = json.loads(row['metainfo'])
                    if isinstance(metainfo, str):
                        metainfo = json.loads(metainfo)
                    keyword_ts = make_tsvector(metainfo)
                    category = guess_metainfo(metainfo)
                    async with writer.transaction():
                        try:
                            if infohash.upper() == infohash:
                                await writer.execute(
                                    '''UPDATE torrent
                                    SET metainfo = $2, category = $3, keyword_ts = $4::tsvector
                                    WHERE infohash = $1''',
                                    infohash, json.dumps(metainfo), category, keyword_ts)
                            else:
                                await writer.execute(
                                    '''DELETE FROM torrent WHERE infohash = $1''',
                                    infohash
                                )
                                await writer.execute(
                                    '''INSERT INTO torrent(infohash, metainfo, category, keyword_ts)
                                    VALUES ($1, $2, $3, $4::tsvector)''',
                                    infohash.upper(), json.dumps(metainfo), category, keyword_ts
                                )
                        except Exception as e:
                            print(e)
                            print(infohash)
                            print(len(keyword_ts))
                            print(keyword_ts)
                            print(e.__dict__)


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    torrent = Torrent()
    loop.run_until_complete(update_tsvector(torrent))



