#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import logging
import asyncio
from backend import crawler
from backend import scrape
from backend import cache
from util import database
'''
    后台任务：
    1. 从dht中获取新的magnet
    2. 更新magnet的tracker信息
'''
if __name__ == '__main__':
    logging.basicConfig(filename='backend.log', level=logging.INFO)
    logging.info('Started')

    loop = asyncio.get_event_loop()
    database = database.Torrent(loop=loop)
    cache = cache.Cache(loop=loop)
    cache.warmup(database)
    scrape = scrape.Scraper(clients=scrape.get_clients(), loop=loop)
    crawler = crawler.Crawler(db_client=database, cache_client=cache, scrape_queue=scrape.task_queue, loop=loop)
    loop.run_until_complete(asyncio.gather(crawler.run(), scrape.run(database)))