#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import sys
import os
import re
from collections import Counter

pattern = r'^【([A-Z][A-Z0-9]+-[0-9]+[A-Z]?)】.*$'
if __name__ == '__main__':
    counter = Counter()
    prefix = Counter()
    for file in os.listdir(sys.argv[1]):
        with open(os.path.join(sys.argv[1], file)) as input:
            for line in input:
                codes = re.findall(pattern, line)
                counter.update(codes)
                prefix.update([c.split('-')[0] for c in codes])

    with open('./data/dict/fhtag.txt', 'wt') as output:
        output.write('tag,count\n')
        for tag, count in prefix.most_common():
            output.write('%s,%d\n' % (tag, count))

    print(len(counter))
    print(counter.most_common())