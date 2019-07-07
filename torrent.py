#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
from pprint import pprint

import chardet
from better_bencode import loads as bdecode


def to_str(bytes):
    encoding = chardet.detect(bytes)['encoding']
    if encoding:
        return bytes.decode(encoding=encoding, errors='ignore')
    else:
        return bytes.decode(errors='ignore')


def metainfo2json(metadata: bytes):

    def to_json(metainfo):
        result = {}
        result['name'] = to_str(metainfo[b'name'])
        if b'files' in metainfo:
            files = []
            for file in metainfo[b'files']:
                if b'path.utf-8' in file:
                    path = (b'/'.join(file[b'path.utf-8'])).decode()
                else:
                    path = to_str(b'/'.join(file[b'path.utf-8']))

                files.append({'path': path, 'length': file[b'length']})

            result['files'] = files
        else:
            result['length'] = metainfo[b'length']

        if b'publisher.utf-8' in metainfo:
            result['publisher'] = metainfo[b'publisher.utf-8'].decode()
        elif b'publisher' in metainfo:
            result['publisher'] = to_str(metainfo[b'publisher'])

        if b'publisher-url.utf-8' in metainfo:
            result['publisher-url'] = metainfo[b'publisher-url.utf-8'].decode()
        elif b'publisher-url' in metainfo:
            result['publisher-url'] = to_str(metainfo[b'publisher-url'])

        return result

    if metadata:
        try:
            metainfo = bdecode(metadata)
            return to_json(metainfo)
        except:
            return None
    else:
        return None


if __name__ == '__main__':
    metadata = open('/Users/sunqf/Downloads/9B8E0D0C226B9482632A17B70FAF437A32DBC526.torrent', 'rb').read()

    jsondata = metainfo2json(metadata)

    pprint(jsondata)