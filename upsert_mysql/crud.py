# 一旦保留
import pymysql.cursors

class crud():
    def __init__(self, 引数):

    def find(selectCulumn, table):
      sql = "SELECT %s FROM %s"
      cursor.execute(sql, (selectCulumn, table))

    def find_specific_value(selectCulumn, table, idname, idvalue):
      sql = "SELECT %s FROM %s WHERE %s = %s"
      cursor.execute(sql, (selectCulumn, table, idname, idvalue))

    def insert_into(table, keys, data):
      for key in keys.keys():
        if keys[0]:
          key += key
          value += value
        else:
          key += ", " + key
          value += ", " + value
      sql = "INSERT INTO %s (%s) VALUES (%s)"
      cursor.execute(sql, (table, key, value))