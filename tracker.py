#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

from urllib import request
import subprocess
import os
from tqdm import tqdm
from better_bencode import load as bdecode

tracker_scrape_urls = {
    # 'torrents_min' : 'magnet:?xt=urn:btih:B3BCB8BD8B20DEC7A30FD9EC43CE7AFAAF631E06',
    'tracker.pirateparty.gr' : 'http://tracker.pirateparty.gr/full_scrape.tar.gz',
    'tracker.leechers-paradise.org' : 'http://tracker.leechers-paradise.org/scrape.tar.gz',
    'coppersurfer.tk' : 'http://coppersurfer.tk/full_scrape_not_a_tracker.tar.gz',
    # 'thepiratebay.org' : 'https://thepiratebay.org/static/dump/csv/torrent_dump_full.csv.gz'
}


best_trackers = 'https://github.com/ngosang/trackerslist/raw/master/trackers_best.txt'


def fetch_file(name, url, local_dir):
    basename = os.path.basename(url)
    local_path = os.path.join(local_dir, basename)
    with tqdm(desc=f'downloading {name}', unit='kb') as download_tqdm:
        request.urlretrieve(url,
                            local_path,
                            reporthook=lambda blocknum, bs, size: download_tqdm.update(bs / 1024))

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
    with open(path, 'rb') as input:
        for infohash, value in bdecode(input)['files']:
            yield infohash, (value['incomplete'], value['complete'], value['downloaded'])


if __name__ == '__main__':

    for name, url in tracker_scrape_urls.items():
        file = fetch_file(name, url, './')
        for data in decode_tracker_scrape(file):
            print(data)