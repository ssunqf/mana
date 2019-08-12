# !/usr/bin/env python
# scrape.py
import binascii
import json
import logging
import os
import random
import struct
from threading import Timer

from tracker.connection import Connection
from tracker.logger import MyLogger
from tracker.utils import Utils


class Tracker:
    def __init__(self, hostname, port, json=False, timeout=15):
        """
        Launches a scraper bound to a particular tracker
        :param hostname: Tracker hostname e.g. coppersuffer.tk
        :param port: 6969, self-explanatory
        :param json: dictates if a json object should be returned as the output
        :param timeout: Timeout value in seconds, program exits if no response received within this period
        """
        self.json = json
        self.timeout = timeout
        self.connection = Connection(hostname, port)

    def _scrape_single_infohash(self, results, connection_id, transaction_id, infohash):
        MyLogger.log("Parsing single string infohash", logging.DEBUG)
        # Validate if string is actually an infohash
        if not Utils.is_40_char_long(infohash):
            logging.warning("Skipping infohash {0}".format(infohash))
            return "Invalid infohash {0}, skipping".format(infohash)
        packet_hashes = bytearray(str(), 'utf-8')
        packet_hashes += binascii.unhexlify(infohash)

        # Send Scrape Request
        packet = struct.pack(">QLL", connection_id, 2, transaction_id) + packet_hashes
        self.connection.sock.send(packet)

        # Receive Scrape Response
        res = self.connection.sock.recv(8 + 12 * len(infohash))

        index = 8
        seeders, completed, leechers = struct.unpack(">LLL", res[index:index + 12])
        results.append(
            {"infohash": infohash, "seeders": seeders, "completed": completed, "leechers": leechers})
        return results

    def _scrape_multiple_infohashes_string_format(self, results, connection_id, transaction_id, infohashes):
        # holds good infohashes for unpacking, used to weed out bad infohashes
        _good_infohashes = list()
        # holds bad error messages
        _bad_results = list()
        # multiple infohashes separated by a comma
        MyLogger.log("Parsing multiple string infohashes", logging.DEBUG)
        infohashes = infohashes.split(",")
        packet_hashes = bytearray(str(), 'utf-8')
        for i, infohash in enumerate(infohashes):
            try:
                packet_hashes += binascii.unhexlify(infohash)
                _good_infohashes.append(infohash)
            except Exception as e:
                _bad_results.append({"infohash": infohash, "error": f'Error: {e}'})
                continue
        packet = struct.pack(">QLL", connection_id, 2, transaction_id) + packet_hashes
        self.connection.sock.send(packet)

        # Scrape response
        res = self.connection.sock.recv(8 + (12 * len(infohashes)))

        index = 8
        for i in range(1, len(infohashes) + 1):
            MyLogger.log("Offset: {} {}".format(index + (i * 12) - 12, index + (i * 12)), logging.DEBUG)
            seeders, completed, leechers = struct.unpack(">LLL", res[index + (i * 12) - 12: index + (i * 12)])
            results.append({"infohash": infohashes[i - 1],
                            "seeders": seeders,
                            "completed": completed,
                            "leechers": leechers})
        results += _bad_results
        return results

    def _scrape_multiple_infohashes_list_format(self, results, connection_id, transaction_id, infohashes):
        MyLogger.log("Parsing list of infohashes", logging.DEBUG)
        # holds good infohashes for unpacking, used to weed out bad infohashes
        _good_infohashes = list()
        # holds bad error messages
        _bad_results = list()
        packet_hashes = bytearray(str(), 'utf-8')
        for i, infohash in enumerate(infohashes):
            try:
                packet_hashes += binascii.unhexlify(infohash)
                _good_infohashes.append(infohash)
            except Exception as e:
                _bad_results.append({"infohash": infohash, "error": f'Error: {e}'})
                continue
        packet = struct.pack(">QLL", connection_id, 2, transaction_id) + packet_hashes
        self.connection.sock.send(packet)

        # Scrape response
        res = self.connection.sock.recv(8 + (12 * len(infohashes)))

        index = 8
        for i in range(1, len(_good_infohashes) + 1):
            MyLogger.log("Offset: {} {}".format(index + (i * 12) - 12, index + (i * 12)), logging.DEBUG)
            seeders, completed, leechers = struct.unpack(">LLL", res[index + (i * 12) - 12: index + (i * 12)])
            results.append({"infohash": infohashes[i - 1],
                            "seeders": seeders,
                            "completed": completed,
                            "leechers": leechers})
        results += _bad_results
        return results

    def scrape(self, infohashes):
        """
        Takes in an infohash, tracker hostname and listening port. Returns seeders, leechers and completed
        information
        :param infohashes: SHA-1 representation of the ```info``` key in the torrent file
        :return: [(infohash, seeders, leechers, completed),...]
        """

        tracker_url = "udp://{0}:{1}".format(self.connection.hostname, self.connection.port)

        # Start a timer
        timer = Timer(self.timeout, exit_program)
        timer.start()

        # quit scraping if there is no connection
        if self.connection.sock is None:
            return "Tracker {0} is down".format(tracker_url)

        # Protocol says to keep it that way
        protocol_id = 0x41727101980

        # We should get the same in response
        transaction_id = random.randrange(1, 65535)

        # Send a Connect Request
        packet = struct.pack(">QLL", protocol_id, 0, transaction_id)
        self.connection.sock.send(packet)

        # Receive a Connect Request response
        res = self.connection.sock.recv(16)
        action, transaction_id, connection_id = struct.unpack(">LLQ", res)

        print(action, transaction_id, connection_id)

        results = list()

        # if infohashes is a string
        if isinstance(infohashes, str):
            # check if it is a single infohash
            if "," not in infohashes:
                # handle single infohashes
                results = self._scrape_single_infohash(results, connection_id, transaction_id, infohashes)
            else:
                # multiple infohashes separated by a comma
                results = self._scrape_multiple_infohashes_string_format(results,
                                                                         connection_id,
                                                                         transaction_id,
                                                                         infohashes)
        elif isinstance(infohashes, list):
            # multiple infohashes list format
            results = self._scrape_multiple_infohashes_list_format(results,
                                                                   connection_id,
                                                                   transaction_id,
                                                                   infohashes)

        timer.cancel()
        results = {"tracker": f'{self.connection.hostname}:{self.connection.port}', "results": results}
        return results

    def __del__(self):
        """
        Close connection if the scraper object is being destroyed
        :return: None
        """
        self.connection.close()

    def __repr__(self):
        return f'{self.connection.hostname}:{self.connection.port}'


def exit_program():
    print("Tracker timed out")
    os._exit(1)
