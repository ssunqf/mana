#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import re
import os
import chardet
from pprint import pprint
from better_bencode import loads as bdecode, dumps as bencode
import mimetypes


def to_str(bytes):
    encoding = chardet.detect(bytes)['encoding']
    return bytes.decode(encoding=encoding)


def metainfo2json(metadata: bytes):

    def to_json(metainfo):
        result = {}
        result['name'] = metainfo[b'name'].decode()
        if b'files' in metainfo:
            files = []
            for file in metainfo[b'files']:
                path = (b'/'.join(file.get(b'path.utf-8') or file.get(b'path')))
                files.append({'path': to_str(path), 'length': file[b'length']})

            result['files'] = files
        else:
            result['length'] = metainfo[b'length']

        if b'publisher.utf-8' in metainfo:
            result['publisher'] = to_str(metainfo[b'publisher.utf-8'])
        elif b'publisher' in metainfo:
            result['publisher'] = to_str(metainfo[b'publisher'])

        if b'publisher-url.utf-8' in metainfo:
            result['publisher-url'] = to_str(metainfo[b'publisher-url.utf-8'])
        elif b'publisher-url' in metainfo:
            result['publisher-url'] = to_str(metainfo[b'publisher-url'])

        return result

    if metadata:
        metainfo = bdecode(metadata)
        return to_json(metainfo)
    else:
        return None


if __name__ == '__main__':
    metadata = open('/Users/sunqf/Downloads/9B8E0D0C226B9482632A17B70FAF437A32DBC526.torrent', 'rb').read()

    jsondata = metainfo2json(metadata)

    pprint(jsondata)