#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
import requests
from tqdm import tqdm
from tracker.tracker import Tracker
from util.database import Torrent

best_trackers = 'https://github.com/ngosang/trackerslist/raw/master/trackers_best_ip.txt'

def get_trackers():
    for _ in range(10):
        res = requests.get(best_trackers)
        if res.status_code == 200:
            continue

        trackers = []
        for url in res.text.split():
            if url.startswith('udp'):
                host, port = url[6:-9].split(':')
                trackers.append((host, int(port)))

        return trackers
    else:
        print('''can't get tracker list''')
        raise RuntimeError()


async def scrape(connections):
    database = Torrent()
    offset = 0
    with tqdm(desc='scrape') as tq:
        while True:
            infohashes = await database.get_infohashes(offset=offset)
            if len(infohashes) == 0:
                break
            offset += len(infohashes)
            tq.update(len(infohashes))

            results = {}
            for start in range(0, len(infohashes), 200):
                for conn in connections:
                    for status in conn.scrape(infohashes[start:start+200])["results"]:
                        infohash = status['infohash']
                        if infohash not in results or results[infohash][1] < status['seeders']:
                            results[infohash] = (infohash, status['seeders'], status['completed'], status['leechers'])

                        print(status)

            await database.update_status(list(results.values()))

if __name__ == '__main__':

    connections = []
    for host, port in get_trackers():
        try:
            conn = Tracker(host, port, json=True, timeout=120)
            connections.append(conn)
        except Exception as e:
            print(e)

    asyncio.get_event_loop().run_until_complete(scrape(connections))