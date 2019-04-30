# coding: UTF-8
import traceback,sys
from time import sleep
import datetime
import connection

def upsert_wp_table():
  mysqlConnect = connection.connect()
  cur = mysqlConnect.connect_mysql()

  with cur as cursor:
    print("開始")
    try:
      postsSql = "SELECT * FROM sc_daily WHERE sc_id = %s"
      cursor.execute(postsSql, (564))
      dailyValues = cursor.fetchone()
      print(dailyValues['sc_date'])
    except:
      print("だめでした")
    finally:
      print("終了っす")

upsert_wp_table()