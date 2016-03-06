# coding=utf-8
import pymysql
from openvj.settings import DB_HOST, DB_USER, DB_PASSWORD, DB_DB


class ObjectDoesNotExist(Exception):
    pass


class MultiObjectReturned(Exception):
    pass


class DBHandler(object):
    def __enter__(self):
        self.connection = pymysql.connect(host=DB_HOST,
                                          user=DB_USER,
                                          password=DB_PASSWORD,
                                          db=DB_DB,
                                          charset="utf8",
                                          cursorclass=pymysql.cursors.DictCursor)
        return self

    def filter(self, sql, args):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, args)
            return cursor.fetchall()

    def get(self, sql, args):
        r = self.filter(sql, args)
        if not r:
            raise ObjectDoesNotExist
        if len(r) > 1:
            raise MultiObjectReturned
        return r

    def _close(self):
        self.connection.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()
