#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
from pprint import pprint
from better_bencode import loads as bdecode, dumps as bencode

def torrent2json(metadata: bytes):

    def to_json(node):
        if isinstance(node, bytes):
            return node.decode()
        elif isinstance(node, list):
            return [to_json(i) for i in node]
        elif isinstance(node, dict):
            return {to_json(k): to_json(v) for k, v in node.items() if k not in [b'pieces', b'piece length']}
        else:
            return node

    if metadata:
        metainfo = bdecode(metadata)
        return to_json(metainfo)
    else:
        return None


if __name__ == '__main__':
    metadata = open('/Users/sunqf/Downloads/9B8E0D0C226B9482632A17B70FAF437A32DBC526.torrent', 'rb').read()

    jsondata = torrent2json(metadata)

    pprint(jsondata)