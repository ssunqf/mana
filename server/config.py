#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = 'private key'

    # ...
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/btsearch?user=sunqf&password=840422'
    SQLALCHEMY_TRACK_MODIFICATIONS = False