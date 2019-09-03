#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import os
import itertools

basedir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(basedir, '../data/dict/av_tag.txt')) as input:
    av_codes = set(line.rsplit(',', maxsplit=1)[0] for line in input.readlines()[1:])
    av_codes = set(itertools.chain.from_iterable([
        map(lambda c: c.upper(), av_codes),
        map(lambda c: c.lower(), av_codes)]))

with open(os.path.join(basedir, '../data/dict/iv_tag.txt')) as input:
    iv_codes = set(line.rsplit(',', maxsplit=1)[0] for line in input.readlines()[1:])
    iv_codes = set(itertools.chain.from_iterable([
        map(lambda c: c.upper(), iv_codes),
        map(lambda c: c.lower(), iv_codes)]))

codes = av_codes.union(iv_codes)

