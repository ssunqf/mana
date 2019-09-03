#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import sys
from parser.patterns import JAV_CODE_PREFIX

jav_codes = set(JAV_CODE_PREFIX.split('|'))

if __name__ == '__main__':
    with open(sys.argv[1]) as input:
        names = {}
        for line in input:
            name, code = line.strip().split(',')
            if not (code.isupper() or code.islower()):
                continue
            code = code[1:-1].lower()
            if code in jav_codes:
                continue

            if code not in names:
                names[code] = set()

            names[code].add(name.lower())

        for k, v in sorted(names.items(), key=lambda x: len(x[1]), reverse=True):
            print(k, v)