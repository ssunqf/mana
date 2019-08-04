#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import re

from ftfy import fixes

from parser.lang import tokenize
from parser.parse import parse
from parser.patterns import spam_patterns


def make_tsvector(metainfo):
    def get_level(ratio):
        levels = [(0.8, 'A'), (0.5, 'B'), (0.3, 'C'), (0, 'D')]
        for thres, level in levels:
            if ratio >= thres:
                return level
        return 'D'

    def is_filter(text):
        return re.search(spam_patterns, text) is not None

    def _each(metainfo):
        yield metainfo['name'], 'A'
        if 'files' in metainfo:
            total_length = sum(file['length'] for file in metainfo['files'])
            for file in sorted(metainfo['files'], key=lambda f: f['length'], reverse=True):
                if not is_filter(file['path']):
                    yield file['path'], get_level(file['length']/total_length)

    vector = {}
    offset = 1
    for file, level in _each(metainfo):
        fields, phrases = parse(file)

        for word in tokenize(file):
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


def make_tsquery(query: str):
    words = tokenize(fixes.fix_character_width(query))
    return ' | '.join(words)


