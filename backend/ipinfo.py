#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import geoip2.database

reader = geoip2.database.Reader('./data/GeoLite2-Country_20190806/GeoLite2-Country.mmdb')


def getCountryCode(ip: str):
    try:
        return reader.country(ip).country.iso_code
    except:
        return None
