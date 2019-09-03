#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import math
import re
import time
import requests
from util.categories import categories
from typing import List

UNITS = [('PB', 10 ** 15), ('TB', 10 ** 12), ('GB', 10 ** 9), ('MB', 10 ** 6), ('KB', 10 ** 3)]


def format_category(category):
    for inter_name, human_name in categories:
        if inter_name == category:
            return human_name
    return '未知'


def format_size(size):
    for unit, divider in UNITS:
        if size >= divider:
            number = re.sub('0+$', '', '%.2f' % (size / divider))
            number = re.sub(r'\.$', '', number)
            return '%s %s' % (number, unit)
    else:
        return '%d B' % size


best_trackers = []

def fetch_trackers():
    global  best_trackers
    best_tracker_url = 'https://github.com/ngosang/trackerslist/raw/master/trackers_best.txt'

    for _ in range(10):
        res = requests.get(best_tracker_url)
        if res.status_code == 200:
            best_trackers = ['tr=' + t for t in res.text.split()]
            break

        time.sleep(120)

fetch_trackers()

if __name__ == '__main__':
    print(format_size(1014766768))
    print(format_size(1000000000))