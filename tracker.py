#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
import aioredis
from urllib import request
import subprocess
import os
from tqdm import tqdm
import mmap
from urllib.parse import quote
from database import Torrent
from torrent import metainfo2json

tracker_scrape_urls = [
    # 'torrents_min' : 'magnet:?xt=urn:btih:B3BCB8BD8B20DEC7A30FD9EC43CE7AFAAF631E06',
    ('tracker.pirateparty.gr', 'udp://tracker.pirateparty.gr:6969/announce', 'http://tracker.pirateparty.gr/full_scrape.tar.gz'),
    ('tracker.leechers-paradise.org', 'udp://tracker.leechers-paradise.org:6969/announce', 'http://tracker.leechers-paradise.org/scrape.tar.gz'),
    ('coppersurfer.tk', 'udp://tracker.coppersurfer.tk:6969/announce', 'http://coppersurfer.tk/full_scrape_not_a_tracker.tar.gz'),
    # 'thepiratebay.org' : 'https://thepiratebay.org/static/dump/csv/torrent_dump_full.csv.gz'
]


def download(url, local_path):
    p = subprocess.Popen(['wget', '-t', 'inf', url, '-O', local_path])
    p.wait()

    return local_path


best_trackers = 'https://github.com/ngosang/trackerslist/raw/master/trackers_best.txt'

request.urlretrieve(best_trackers, '/tmp/trackers_best.txt')
tmp_tracker_file = download(best_trackers, '/tmp/trackers_best.txt')

with open(tmp_tracker_file) as input:
    urls = set([line.strip() for line in input.readlines() if len(line.strip()) > 0] + \
           [url for _, url, _ in tracker_scrape_urls])
    tracker_best_urls = ['&tr=' + quote(url.strip(), safe='') for url in urls]


def fetch_file(name, url, local_dir):
    basename = os.path.basename(url)
    local_path = os.path.join(local_dir, basename)
    with tqdm(desc=f'downloading {name}', unit='kb') as download_tqdm:
        download(url, local_path)

    if basename.endswith(".tar.gz"):
        p = subprocess.Popen(['tar', 'xf', basename], cwd=local_dir)
        p.wait()
        os.remove(local_path)
        return os.path.join(local_dir, 'scrape')

    elif local_path.endswith(".gz"):
        p = subprocess.Popen(['gunzip', '-f', basename], cwd=local_dir)
        p.wait()
        return os.path.join(local_dir, basename[:-3])


def decode_tracker_scrape(path):

    def _decode(mm):

        if mm[:9] != b'd5:filesd' and mm[-1] != b'e':
            raise

        offset = 9
        while mm[offset:offset+1] != b'e':
            if mm[offset:offset+3] != b'20:':
                break

            offset += 3
            infohash = mm[offset:offset+20]
            offset += 20

            infos = {}

            if mm[offset:offset + 1] != b'd':
                break
            offset += 1

            while mm[offset:offset+1] != b'e':
                end = mm.find(b':', offset+1)
                size = int(mm[offset:end])
                offset = end + 1

                key = mm[offset:offset+size]
                offset += size

                if mm[offset:offset+1] != b'i':
                    raise
                offset += 1

                end = mm.find(b'e', offset+1)
                value = int(mm[offset:end])
                offset = end + 1

                infos[key.decode()] = value

            offset += 1

            yield infohash.hex(), infos

    with open(path, 'rb') as input:
        mm = mmap.mmap(input.fileno(), 0, prot=mmap.PROT_READ)
        yield from _decode(mm)


loop = asyncio.get_event_loop()
redis_client = loop.run_until_complete(
    aioredis.create_redis_pool('redis://localhost'))

db_client = Torrent(loop)
INFOHASH_FOUND = 'INFOHASH_FOUND'

torrent_dir = './torrents'
os.makedirs(torrent_dir, exist_ok=True)


def fetch_metadata(buffer):
    tmp_magnet = os.path.join(torrent_dir, 'magnet.tmp')
    with open(tmp_magnet, 'wt') as input:
        for infohash, num_peers in buffer:
            input.write('magnet:?xt=urn:btih:{}{}\n'.format(
                infohash, ''.join(tracker_best_urls)))

    p = subprocess.Popen(['aria2c',
                          '-d', torrent_dir,
                          '-i', tmp_magnet,
                          '--bt-metadata-only=true',
                          '--bt-save-metadata=true',
                          '-j 200',
                          '-x 4'
                          ], cwd='./')
    try:
        p.wait(2400)
    except:
        p.kill()

    for infohash, num_peers in buffer:
        path = os.path.join(torrent_dir, infohash + '.torrent')
        if os.path.exists(path):
            try:
                with open(path, 'rb') as input:
                    metadata = input.read()
                info = metainfo2json(metadata)
                if info:
                    loop.run_until_complete(db_client.save_torrent([(infohash, info)]))
                    loop.run_until_complete(redis_client.sadd(INFOHASH_FOUND, bytes.fromhex(infohash)))
                os.remove(path)
            except Exception as e:
                print(e)


async def warmup():
    for infohash in tqdm(await db_client.get_all(), desc='warmup cache'):
        await redis_client.sadd(INFOHASH_FOUND, bytes.fromhex(infohash))

# loop.run_until_complete(warmup())

if __name__ == '__main__':
    '''
    
        file = fetch_file(name, url, './')
        for data in decode_tracker_scrape(file):
            print(data)
    '''

    for name, tracker_url, download_url in tracker_scrape_urls:
        scrape_file = fetch_file(name, download_url, './torrents/')

        buffer = []
        for infohash, infos in decode_tracker_scrape(scrape_file):
            if loop.run_until_complete(
                    redis_client.sismember(INFOHASH_FOUND, bytes.fromhex(infohash))):
                continue
            num_peers = infos['complete'] + infos['incomplete']
            if num_peers >= 10:
                buffer.append((infohash, num_peers))

            if len(buffer) > 10000:
                buffer = sorted(buffer, key=lambda p: p[1], reverse=True)

                fetch_metadata(buffer)

                buffer = []

        if len(buffer) > 0:
            fetch_metadata(buffer)
