#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-


from util.database import Torrent

async def build():
    torrent = Torrent()

    while True:
        batch = await torrent.foreach()