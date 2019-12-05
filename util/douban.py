#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import requests
from collections import namedtuple
import json
import time
from bs4 import BeautifulSoup


class Tag:
    def __init__(self, name, url):
        self.name = name
        self.url = url


class Type:
    def __init__(self, name, tags):
        self.name = name
        self.tags = tags
        self.name2tag = {t.name: t for t in self.tags}

    def get_tag(self, tag):
        return self.name2tag[tag]

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.tags[item]
        elif isinstance(item, str):
            return self.name2tag[item]
        elif isinstance(item, slice):
            return self.tags[item]
        else:
            raise KeyError(item)

movie_tags = [
        Tag('热门', 'https://movie.douban.com/j/search_subjects?type=movie&tag=热门&sort=recommend&page_limit=100&page_start=0'),
        Tag('高分', 'https://movie.douban.com/j/search_subjects?type=movie&tag=豆瓣高分&sort=time&page_limit=100&page_start=0'),
        Tag('经典', 'https://movie.douban.com/j/search_subjects?type=movie&tag=经典&sort=time&page_limit=100&page_start=0'),
        Tag('冷门佳片', 'https://movie.douban.com/j/search_subjects?type=movie&tag=冷门佳片&sort=recommend&page_limit=100&page_start=0'),
        Tag('华语', 'https://movie.douban.com/j/search_subjects?type=movie&tag=华语&sort=recommend&page_limit=100&page_start=0'),
        Tag('欧美', 'https://movie.douban.com/j/search_subjects?type=movie&tag=欧美&sort=recommend&page_limit=100&page_start=0'),
        Tag('韩国', 'https://movie.douban.com/j/search_subjects?type=movie&tag=韩国&sort=recommend&page_limit=100&page_start=0'),
        Tag('日本', 'https://movie.douban.com/j/search_subjects?type=movie&tag=日本&sort=recommend&page_limit=100&page_start=0'),
    ]

tv_tags = [
    Tag('热门', 'https://movie.douban.com/j/search_subjects?type=tv&tag=热门&sort=recommend&page_limit=100&page_start=0'),
    Tag('美剧', 'https://movie.douban.com/j/search_subjects?type=tv&tag=美剧&sort=recommend&page_limit=100&page_start=0'),
    Tag('英剧', 'https://movie.douban.com/j/search_subjects?type=tv&tag=英剧&sort=recommend&page_limit=100&page_start=0'),
    Tag('韩剧', 'https://movie.douban.com/j/search_subjects?type=tv&tag=韩剧&sort=recommend&page_limit=100&page_start=0'),
    Tag('日剧', 'https://movie.douban.com/j/search_subjects?type=tv&tag=日剧&sort=recommend&page_limit=100&page_start=0'),
    Tag('国产剧', 'https://movie.douban.com/j/search_subjects?type=tv&tag=国产剧&sort=recommend&page_limit=100&page_start=0'),
    Tag('港剧', 'https://movie.douban.com/j/search_subjects?type=tv&tag=港剧&sort=recommend&page_limit=100&page_start=0')
]

cartoon_tags = [
    Tag('日本', 'https://movie.douban.com/j/search_subjects?type=tv&tag=日本动画&sort=recommend&page_limit=100&page_start=0')
]

resources = {
    '电影': Type('电影', movie_tags),
    '电视': Type('电视', tv_tags),
    '动画': Type('动画', cartoon_tags)
}

DOUBAN_KEY = 'DOUBAN'

KEY_TEMPLATE = 'DOUBAN_%s_%s'

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def fetch_data(cache):
    for type in resources.values():
        for tag in type.tags:
            while True:
                response = requests.get(tag.url, headers=headers)
                if response.status_code == 200:
                    tag.data = json.loads(response.text)['subjects']
                    cache.set(KEY_TEMPLATE % (type.name, tag.name), tag.data)
                    break
                time.sleep(10)


if __name__ == '__main__':

    for type in resources.values():
        for tag in type.tags:
            print(tag)
