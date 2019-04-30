# coding: UTF-8
import pymysql.cursors
import traceback,sys
import settings

class connect():
  def connect_mysql(self):
    HOST_NAME = settings.HST
    USER_NAME = settings.USN
    PASSWORD = settings.PWD
    DB_NAME = settings.DSN

    conn = pymysql.connect(
      host = HOST_NAME,
      user = USER_NAME,
      password = PASSWORD,
      db = DB_NAME,
      charset = 'utf8',
      cursorclass = pymysql.cursors.DictCursor)
    return conn