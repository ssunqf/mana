#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import os
import sys
import time
from tqdm import tqdm
from typing import List
import subprocess
import asyncio
import aioredis
from crawler.cache import Cache
from urllib import request
from urllib.parse import quote
from util.database import Torrent
from util.torrent import metainfo2json

tracker_scrape_urls = [
    # 'torrents_min' : 'magnet:?xt=urn:btih:B3BCB8BD8B20DEC7A30FD9EC43CE7AFAAF631E06',
    (
        'tracker.pirateparty.gr',
        'udp://tracker.pirateparty.gr:6969/announce',
        'http://tracker.pirateparty.gr/full_scrape.tar.gz'
    ),
    (
        'tracker.leechers-paradise.org',
        'udp://tracker.leechers-paradise.org:6969/announce',
        'http://tracker.leechers-paradise.org/scrape.tar.gz'
    ),
    (
        'coppersurfer.tk',
        'udp://tracker.coppersurfer.tk:6969/announce',
        'http://coppersurfer.tk/full_scrape_not_a_tracker.tar.gz'
    ),
    # 'thepiratebay.org' : 'https://thepiratebay.org/static/dump/csv/torrent_dump_full.csv.gz'
]


def download(url, local_path):
    p = subprocess.Popen(['wget', '-t', 'inf', url, '-O', local_path])
    p.wait()
    return local_path if os.path.exists(local_path) else None


loop = asyncio.get_event_loop()
cache = Cache(loop)
database = Torrent(loop)
cache.warmup(database)

INFOHASH_FOUND = 'INFOHASH_FOUND'

torrent_dir = './torrents'
os.makedirs(torrent_dir, exist_ok=True)

best_trackers = 'https://github.com/ngosang/trackerslist/raw/master/trackers_best.txt'

request.urlretrieve(best_trackers, '/tmp/trackers_best.txt')
tmp_tracker_file = download(best_trackers, '/tmp/trackers_best.txt')

with open(tmp_tracker_file) as input:
    urls = set([line.strip() for line in input.readlines() if len(line.strip()) > 0] + \
           [url for _, url, _ in tracker_scrape_urls])
    tracker_best_urls = ['&tr=' + quote(url.strip(), safe='') for url in urls]


async def download_metadata(infohashs: List[str]):
    tmp_magnet = os.path.join(torrent_dir, 'magnet.tmp')
    with open(tmp_magnet, 'wt') as input:
        for infohash in infohashs:
            input.write('magnet:?xt=urn:btih:{}{}\n'.format(
                infohash, ''.join(tracker_best_urls)))

    p = subprocess.Popen(['aria2c',
                          '-d', torrent_dir,
                          '-i', tmp_magnet,
                          '--bt-metadata-only=true',
                          '--bt-save-metadata=true',
                          '--bt-stop-timeout=600',
                          '--max-concurrent-downloads=500',
                          '--max-connection-per-server=8',
                          ])
    try:
        p.wait()
    except Exception as e:
        print(e)
    finally:
        p.terminate()

    for infohash in infohashs:
        path = os.path.join(torrent_dir, infohash.lower() + '.torrent')
        if os.path.exists(path):
            try:
                with open(path, 'rb') as input:
                    metadata = input.read()
                info = metainfo2json(metadata)
                if info:
                    await database.save_torrent([(infohash, info)])
                    await cache.cache_infohash(infohash)
                os.remove(path)
            except Exception as e:
                print(e)

if __name__ == '__main__':

    # loop.run_until_complete(warmup())

    buffer = []
    for line in sys.stdin:
        infohash = line.split()[0]

        if not loop.run_until_complete(cache.find_infohash(infohash)):
            buffer.append(infohash)

            if len(buffer) > 10000:
                loop.run_until_complete(download_metadata(buffer))

                buffer = []

    if len(buffer) > 0:
        download_metadata(buffer)

