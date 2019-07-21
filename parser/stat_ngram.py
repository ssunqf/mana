#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import re
import asyncio
from util.database import Torrent
from parser.parse import parse
from parser.lang import extract
from parser.patterns import spam_patterns
import json


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
        print(file)
        print(fields)
        for phrase in phrases:
            for lang, lang_phrases in extract(phrase).items():
                for p in lang_phrases:
                    for id, token in enumerate(p.split()):
                        if token not in vector:
                            vector[token] = ['%d%s' % (offset, level)]
                        else:
                            vector[token].append('%d%s' % (offset, level))

                        offset += 1
                    # 分割不连续的短语
                    offset += 1

    def to_str(v):
        res = []
        for token, pos in v.items():
            res.append(token + ':' + ','.join(pos))

        return ' '.join(res)

    return to_str(vector)


async def update_tsvector(torrent):
    async with torrent.pool.acquire() as reader:
        async with torrent.pool.acquire() as writer:
            async with reader.transaction():
                async for row in reader.cursor('SELECT infohash, metainfo FROM torrent ORDER BY infohash'):
                    metainfo = json.loads(row['metainfo'])
                    if isinstance(metainfo, str):
                        metainfo = json.loads(metainfo)
                    keyword_ts = make_tsvector(metainfo)
                    async with writer.transaction():
                        try:
                            await writer.execute(
                                '''UPDATE torrent
                                SET metainfo = $1, keyword_ts = $2::tsvector
                                WHERE infohash = $3''',
                                json.dumps(metainfo), keyword_ts, row['infohash'])
                        except Exception as e:
                            print(e)
                            print(e.__dict__)


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    torrent = Torrent()
    loop.run_until_complete(update_tsvector(torrent))



