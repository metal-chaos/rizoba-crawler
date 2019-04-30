# -----------------------------------
# 概要："wp_posts"テーブルに対する公開・非公開の処理
# -----------------------------------

# coding: UTF-8
import traceback,sys
from time import sleep
import datetime
from distinct import distinctValue as dV
import connection

def decide_private_publish(dateKey):
  mysqlConnect = connection.connect()
  conn = mysqlConnect.connect_mysql()
  cur = conn.cursor()

  updatePublish = "publish"
  updatePrivate = "private"
  updateType = "post"

  sleep(2)

  now = datetime.datetime.now()

  with cur as cursor:
    try:
      # -----------------------------------
      # 非公開にする処理
      # -----------------------------------
      postsSql = "UPDATE wp_posts SET post_status = %s WHERE post_type = %s"
      cursor.execute(postsSql, (updatePrivate, updateType))

      # -----------------------------------
      # 公開にする処理
      # -----------------------------------
      # "sc_daily"テーブルから最新の年月日（クローリングした日）が格納されたデータを取得
      dailySql = "SELECT * FROM sc_daily WHERE date_key = %s"
      cursor.execute(dailySql, (dateKey))
      dailyValues = cursor.fetchall()
      for dailyValue in dailyValues:
        # "sc_daily"テーブルからpostnameを取得
        dailyPostname = str(dailyValue['post_name'])
        # "wp_posts"テーブルからpostnameが同じ行をUPDATE
        postsSql = "UPDATE wp_posts SET post_status = %s WHERE post_name = %s"
        cursor.execute(postsSql, (updatePublish, dailyPostname))
      # オートコミットじゃないので、明示的にコミットを書く必要がある
      conn.commit()
    except:
      dV.exception_error_log()
    finally:
      conn.close()