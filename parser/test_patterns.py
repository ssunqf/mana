#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import unittest
from parser.patterns import *

def test_normalize_code():
    test = 'ktra-114'
    assert normalize_jav_code(test) == test