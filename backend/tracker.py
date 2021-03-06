#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
from urllib import request
import subprocess
import os
from tqdm import tqdm
import mmap
from backend.cache import Cache
from urllib.parse import quote
from util.database import Torrent
from util.torrent import metainfo2json

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

tracker_scrape_urls = [
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
    while True:
        p = subprocess.Popen(['curl', '-o', local_path, url])
        p.wait()
        if p.returncode == 18:
            import time
            time.sleep(30)
            continue
        return local_path if os.path.exists(local_path) else None


def fetch_scrape_file(name, url, local_dir):
    basename = os.path.basename(url)
    local_path = os.path.join(local_dir, basename)
    if not download(url, local_path):
        return None

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
cache = Cache(loop)
db_client = Torrent(loop=loop)

cache.warmup(db_client)

INFOHASH_FOUND = 'INFOHASH_FOUND'

torrent_dir = './torrents'
os.makedirs(torrent_dir, exist_ok=True)

trackers_best = 'https://github.com/ngosang/trackerslist/raw/master/trackers_best_ip.txt'

tmp_tracker_file = download(trackers_best, '/tmp/trackers_best.txt')

with open(tmp_tracker_file) as input:
    urls = set([line.strip() for line in input.readlines() if len(line.strip()) > 0] + \
           [url for _, url, _ in tracker_scrape_urls])
    tracker_best_urls = ['&tr=' + quote(url.strip(), safe='') for url in urls]


async def download_metadata(infohashes):
    tasks = []
    step = len(infohashes)//5
    for offset in range(0, len(infohashes), step):
        tmp_magnet = os.path.join(torrent_dir, 'magnet.tmp.%d' % offset)
        with open(tmp_magnet, 'wt') as input:
            for infohash in infohashes[offset:offset+step]:
                input.write('magnet:?xt=urn:btih:{}{}\n'.format(
                    infohash,
                    ''.join(tracker_best_urls)
                ))

        p = subprocess.Popen(['aria2c',
                              '-d', torrent_dir,
                              '-i', tmp_magnet,
                              '--bt-metadata-only=true',
                              '--bt-save-metadata=true',
                              '--follow-torrent=false',
                              '--seed-time=0',
                              '--bt-stop-timeout=600',
                              '--max-concurrent-downloads=500',
                              '--max-connection-per-server=16',
                              # '--optimize-concurrent-downloads=true',
                              '--bt-tracker', ','.join(urls),
                              '--enable-dht=true',
                              # '--bt-enable-lpd=true',
                              '--enable-peer-exchange=true'
                              ])
        tasks.append(p)

    for task in tasks:
        try:
            task.wait()
        except:
            task.kill()

    for infohash in infohashes:
        path = os.path.join(torrent_dir, infohash.lower() + '.torrent')
        if os.path.exists(path):
            try:
                with open(path, 'rb') as input:
                    metadata = input.read()
                info = metainfo2json(metadata)
                if info:
                    await db_client.save_torrent([(infohash, info)])
                    await cache.cache_infohash(infohash)
                os.remove(path)
            except Exception as e:
                print(e)


async def fetch_stats(batch_size=5000):
    no_exists = {}
    successed = []
    for name, tracker_url, download_url in tracker_scrape_urls:
        try:
            scrape_file = fetch_scrape_file(name, download_url, torrent_dir)

            if not scrape_file:
                continue

            with open(os.path.join(torrent_dir, name), 'wt') as output:
                for infohash, infos in decode_tracker_scrape(scrape_file):
                    infohash = infohash.upper()
                    if not await cache.find_infohash(infohash):
                        no_exists[infohash] = max(infos['complete'] + infos['incomplete'],
                                                  no_exists.get(infohash, 0))

                    output.write(f'%s\t%d\t%d\t%d\n' % (
                        infohash, infos['complete'], infos['downloaded'], infos['incomplete']))

            successed.append(os.path.join(torrent_dir, name))
        except Exception as e:
            print(e)
            print(name, tracker_url, download_url)

    print('not exist ', len(no_exists))
    infohashs = [infohash for infohash, _ in sorted(no_exists.items(), key=lambda i:i[1], reverse=True)]
    for offset in range(0, len(infohashs), batch_size):
        await download_metadata(infohashs[offset:offset+batch_size])

    # merge
    prev = [(open(n), None) for n in successed]
    buff = []
    while len(prev) > 0:

        curr = []
        for fp, item in prev:
            if item is None:
                fields = fp.readline().strip().split()
                if len(fields) == 4:
                    infohash, c, d, i = fields[0], int(fields[1]), int(fields[2]), int(fields[3])
                    curr.append((fp, (infohash, c, d, i)))
            else:
                curr.append((fp, item))

        if len(curr) == 0:
            break

        small = min(curr, key=lambda i:i[1][0])[1]

        prev = []
        for fp, item in curr:
            if small[0] < item[0]:
                prev.append((fp, item))
            else:
                small = (small[0], max(small[1], item[1]), max(small[2], item[2]), max(small[3], item[3]))
                prev.append((fp, None))

        buff.append(small)
        if len(buff) > 10000:
            await db_client.update_status(buff)
            buff = []

    if len(buff) > 0:
        await db_client.update_status(buff)
