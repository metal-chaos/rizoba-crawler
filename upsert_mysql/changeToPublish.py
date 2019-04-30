# -----------------------------------
# 概要："wp_posts"テーブルに対する公開・非公開の処理
# -----------------------------------

# coding: UTF-8
import traceback,sys
from time import sleep
import datetime
from distinct import distinctValue as dV
import connection

upHomeUrl = "https://resorn.net/"
upContent = "テスト（2018/08/25）2回目"
upTitle = "テスト（2018/08/25）2回目"
upSlug = "detail"
upMenuOrder = 5555

def upsert_wp_table(pmPostId, pmValue, dateKey):
  mysqlConnect = connection.connect()
  conn = mysqlConnect.connect_mysql()
  cur = conn.cursor()

  updatePublish = "publish"
  updatePrivate = "private"

  sleep(2)

  now = datetime.datetime.now()

  with cur as cursor:
    try:
      # -----------------------------------
      # 全て公開にする処理
      # -----------------------------------
      postsSql = "UPDATE wp_posts SET post_status = %s"
      cursor.execute(postsSql, (updatePublish))

      # オートコミットじゃないので、明示的にコミットを書く必要がある
      conn.commit()
    except:
      dV.exception_error_log()
    finally:
      conn.close()
  
    
upsert_wp_table(pmPostId = 19314, pmValue = "FALSE", dateKey = "2018-09-24")