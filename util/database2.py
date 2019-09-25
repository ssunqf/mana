#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import logging
import psycopg2
from psycopg2 import pool
from parser.search import make_tsvector, make_tsquery

class Torrent:
    def __init__(self, host='localhost'):
        self.conn_pool = psycopg2.pool.ThreadedConnectionPool(1, 20, user="sunqf",
                                           password="840422",
                                           host=host,
                                           port="5432",
                                           database="btsearch")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn_pool.closeall()

    def search(self, query, offset=0, limit=20, max_size=1000, **kwargs):

        conn = self.conn_pool.getconn()

        try:

            cursor = conn.cursor()

            query = make_tsquery(query)
            conditions = ' and '.join([('%s=%d' if isinstance(v, int) else '%s=\'%s\'') % (k, v)
                                       for k, v in kwargs.items()])
            cmd = f'''
                SELECT *, COUNT(*) OVER() AS total
                FROM (
                    SELECT *, keyword_ts <=> \'{query}\'::tsquery AS rank
                    FROM torrent
                    WHERE keyword_ts @@ \'{query}\'::tsquery {'and ' + conditions if len(kwargs) > 0 else ''}
                    ORDER BY keyword_ts <=> \'{query}\'::tsquery
                    LIMIT {max_size}
                ) AS matched
                WHERE rank < 5
                ORDER BY rank, seeders DESC
                LIMIT {limit} OFFSET {offset}
                '''
            cursor.execute(cmd)

            records = cursor.fetchall()
            return self.friendly(cursor, records)
        except Exception as e:
            logging.warning(e)
            raise e
        finally:
            self.conn_pool.putconn(conn)

    def get_by_infohash(self, infohash):
        conn = self.conn_pool.getconn()

        try:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT infohash, metainfo, category, seeders, completed, leechers, update_time
                FROM torrent
                WHERE infohash = '%s'
                ''' % infohash.upper())
            records = cursor.fetchall()

            return self.friendly(cursor, records)
        except Exception as e:
            raise e
        finally:
            self.conn_pool.putconn(conn)

    def friendly(self, cursor, records):
        return [{col.name: value for col, value in zip(cursor.description, record)} for record in records]

    def update(self, keywords):
        conn = self.conn_pool.getconn()

        try:
            for keyword in keywords:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    update torrent set adult = TRUE
                    where adult = FALSE AND  keyword_ts @@ '%s'::tsquery and metainfo::text ~* '%s[-]*\d{3,6}' 
                    ''' % (keyword, keyword))
        except Exception as e:
            raise e
        finally:
            self.conn_pool.putconn(conn)


if __name__ == '__main__':
    db = Torrent('207.148.124.42')

    print(db.get_by_infohash('0000C1B9D879DF74C352D5481CEB6A7FBEBBCFBE'))

    print(db.search('高树'))

    with open('../data/dict/names.txt') as input:
        names = [line.strip() for line in input.readlines()]
        db.update(names)