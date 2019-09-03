#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = 'private key'

    SEND_FILE_MAX_AGE_DEFAULT = timedelta(seconds=1)

    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

    # ...
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://localhost/btsearch?user=sunqf&password=840422'
    SQLALCHEMY_TRACK_MODIFICATIONS = False