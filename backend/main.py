#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import logging
import click

'''
    后台任务：
    1. 从dht中获取新的magnet
    2. 更新magnet的tracker信息
'''
@click.command()
@click.option('--warmup', default=1, help='warmup redis')
@click.option('--crawler-port', default=6881, help='crawler port')
@click.option('--scrape-port', default=8818, help='scrape port')
def start(warmup, crawler_port, scrape_port):
    import asyncio
    from backend import crawler
    from backend import scrape
    from backend import cache
    from util import database

    loop = asyncio.get_event_loop()
    database = database.Torrent(loop=loop)
    cache = cache.Cache(loop=loop)
    if warmup:
        cache.warmup(database)
    scrape = scrape.Scraper(clients=scrape.get_clients(), loop=loop)
    crawler = crawler.Crawler(db_client=database, cache_client=cache, scrape_queue=scrape.task_queue, loop=loop)
    loop.run_until_complete(asyncio.gather(crawler.run(port=crawler_port), scrape.run(database, port=scrape_port)))


if __name__ == '__main__':
    logging.basicConfig(filename='backend.log', level=logging.INFO)
    logging.info('Started')
    start()

