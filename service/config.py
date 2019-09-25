#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = 'private key'

    SEND_FILE_MAX_AGE_DEFAULT = timedelta(seconds=1)

    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 240 * 60 * 60
    CACHE_KEY_PREFIX = 'cilichong'