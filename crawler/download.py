#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import os
import sys
import time
from tqdm import tqdm
import subprocess

from typing import List
from pprint import pprint

import logging

from pyaria2 import Aria2RPC


def fetch_metadata(aria_client, uris: List[str], output_dir):
    gids = []

    for uri in uris:
        gid = aria_client.addUri([uri],
            options={
                'bt-metadata-only': 'true',
                'bt-save-metadata': 'true',
                'max-tries': '5',
                'retry-wait': '10',
                'dir': output_dir
            })

        gids.append(gid)

    while len(gids) > 0:
        left = []
        for gid in gids:
            try:
                response = aria_client.tellStatus(gid)
                if response['status'] == 'complete':
                    if response['totalLength'] == response['completedLength']:
                        infohash = response['infoHash']
                        output_dir = response['dir']
                        file = os.path.join(output_dir, infohash + '.torrent')
                        with open(file, 'rb') as input:
                            data = input.read()
                            yield infohash, data
                    aria_client.removeDownloadResult(gid)
                elif response['status'] in ['waiting', 'active', 'pause']:
                    left.append(gid)
                elif response['status'] in ['error', 'removed']:
                    aria_client.removeDownloadResult(gid)
            except Exception as e:
                logging.exception(e)

        logging.info(aria_client.getGlobalStat())
        if len(left) == len(gids):
            time.sleep(20)
        gids = left


if __name__ == '__main__':

    aria_server = subprocess.Popen([
        'aria2c',
        '--enable-rpc',
        '--rpc-listen-all=true',
        '--rpc-allow-origin-all',
        '--max-concurrent-downloads=500',
        '--max-connection-per-server=20',
        '--bt-stop-timeout=600'
    ])

    time.sleep(10)

    aria_client = Aria2RPC(url='http://localhost:6800/rpc', token='dht')

    with open(sys.argv[1]) as input:
        uris = input.readlines()
        for infohash, metainfo in fetch_metadata(aria_client, uris, './torrents'):
            print(infohash, metainfo)

    aria_server.kill()