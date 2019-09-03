#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import re

from ftfy import fixes

from parser.lang import tokenize
from parser.parse import parse
from parser.patterns import spam_patterns
from util.torrent import build_dir_tree


def make_tsvector(metainfo):
    def get_level(ratio):
        levels = [(0.8, 'A'), (0.5, 'B'), (0.3, 'C'), (0, 'D')]
        for thres, level in levels:
            if ratio >= thres:
                return level
        return 'D'

    def is_filter(text):
        return re.search(spam_patterns, text) is not None

    vector = {}
    offset = 1
    if 'length' not in metainfo:
        metainfo['length'] = sum(file['length'] for file in metainfo['files'])
    total_length = metainfo['length']
    for dir in build_dir_tree(metainfo).traversal():
        if is_filter(dir.name):
            continue

        level = get_level(dir.length / total_length)
        fields, phrases = parse(dir.name)

        for word in tokenize(dir.name):
            if len(word) > 100:
                print(word)
            if word not in vector:
                vector[word] = ['%d%s' % (offset, level)]
            else:
                vector[word].append('%d%s' % (offset, level))

            offset += 1

        offset += 1

        '''
        for phrase in phrases:
            for id, word in enumerate(tokenize(phrase)):
                if word not in vector:
                    vector[word] = ['%d%s' % (offset, level)]
                else:
                    vector[word].append('%d%s' % (offset, level))

                offset += 1
            # 分割不连续的短语
            offset += 1
        '''

    def to_str(v):
        res = []
        for token, positions in v.items():
            if len(positions) > 200:
                positions = sorted(positions, key=lambda x:x[-1])
            res.append(token + ':' + ','.join(positions[:200]))
        return ' '.join(res)

    return to_str(vector)


stopwords = {'的', '了'}

def make_tsquery(query: str):
    words = tokenize(fixes.fix_character_width(query))
    return ' | '.join([word for word in words if word not in stopwords])


if __name__ == '__main__':
    print(make_tsquery('|| && ----:'))