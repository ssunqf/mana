#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import asyncio
import aiohttp

import better_bencode

from bs4 import BeautifulSoup

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

import cfscrape

scraper = cfscrape.create_scraper()  # returns a CloudflareScraper instance
# Or: scraper = cfscrape.CloudflareScraper()  # CloudflareScraper inherits from requests.Session
data = scraper.get("http://itorrents.org/torrent/B415C913643E5FF49FE37D304BBB5E6E11AD5101.torrent").content  # => "<!DOCTYPE html><html><head>..."
print(data)

async def fetch_from_url(infohash):
    url = f'http://itorrents.org/torrent/{infohash}.torrent'
    headers = {
        'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html)'
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            print(response.real_url)
            print(response.content_type)
            raw_data = await response.read()
            print(raw_data)
            if response.content_type == 'application/x-bittorrent':
                print(raw_data)
                print(better_bencode.loads(raw_data))
                return raw_data
            else:
                html = BeautifulSoup(raw_data)
                #html.select('')
                return None


asyncio.get_event_loop().run_until_complete(fetch_from_url('9B8E0D0C226B9482632A17B70FAF437A32DBC526'))