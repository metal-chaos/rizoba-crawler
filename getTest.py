# coding: UTF-8
import traceback,sys
from time import sleep
import datetime
import connection

scDailyValue = {
    "id": "48",
    "prefectures_name": "bbb",
    "prefectures_slug": "aaa",
  }

def insert_into(table, keys):
  mysqlConnect = connection.connect()
  conn = mysqlConnect.connect_mysql()
  cur = conn.cursor()

  with cur as cursor:
    tableKey = ""
    tableValue = ""
    for key in keys.keys():
      if key[-1]:
        tableKey += key
        tableValue += keys[key]
      else:
        tableKey += key + ", "
        tableValue += keys[key] + ", "
    sql = "INSERT INTO %s (%s, %s) VALUES (%s, %s)"
    print(tableKey)
    print(tableValue)
    cursor.execute(sql, (table, tableKey, tableValue))
    conn.commit()
    conn.close()

insert_into("sc_prefectures", scDailyValue)