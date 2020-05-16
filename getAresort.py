# coding: UTF-8
import requests
import re
from bs4 import BeautifulSoup
from lxml import html
from time import sleep
import pymysql.cursors
import datetime
from distinct import distinctValue as dV
from processing import main, aresort
from upsert_mysql import sc_daily as usDaily
from upsert_mysql import refrectScDataToWp as toWp
from upsert_mysql import decidePrivatePublish as decidePP
import traceback,sys
import random
import settings

"""
Global variable
"""
homeUrl = settings.AR_HOME_URL
listUrl = "https://www.a-resort.jp/resort/ankens/search/?page="
dateKey = datetime.datetime.now().strftime('%Y-%m-%d')

def aresort_page_list():
  """
  Get information from job lists
  """

  pNumber = 1

  while True:
    if pNumber == 11 or pNumber == 31:
      pNumber += 3
    print("アルファ求人一覧「" + str(pNumber) + "」ページ目の情報を取得中…")
    sleep(random.randint(1,8))

    try:
      arHtml = requests.get(listUrl + str(pNumber), timeout = 30)
      arSoup = BeautifulSoup(arHtml.text, 'html.parser')
    except:
      dV.exception_error_log()

    # 求人詳細へのリンクを全て取得
    allDtlLink = arSoup.select('div.works_list_link > a')
    for eachDtlLink in allDtlLink:
      bfDtlLink = re.search(r"(\/resort\/ankens\/view/\?id=\d+)", str(eachDtlLink))
      afDtlLink = homeUrl + bfDtlLink.group(0)
      # 求人詳細の実行
      try:
        aresort_page_detail(afDtlLink)
      except:
        dV.exception_error_log()

    # ページネーションから処理終了か判断、item_page_linkへのリンクを全て取得
    if pNumber == 1:
      pNumber += 1
    else:
      forReLink = arSoup.findAll("a", title= "Last")[1].text.translate(str.maketrans({"[": None, "]": None})) # 最後の番号を取得
      if int(forReLink) > pNumber:
        pNumber += 1
      else:
        decidePP.decide_private_publish(dateKey)
        break

def aresort_page_detail(afDtlLink):
  """Get information from detail pages

  Args:
    afDtlLink (str): URL of a job detail page
  """

  print("アルファ求人詳細「" + afDtlLink + "」の情報を取得中…")
  sleep(random.randint(1,8))

  detailHtml = requests.get(afDtlLink, timeout = 5)
  detailSoup = BeautifulSoup(detailHtml.text, 'html.parser')
  datas = {}

  # 求人詳細のスクレイピング
  processing = aresort.Aresort(detailSoup, afDtlLink)
  primary = main.Main()
  datas = primary.make_processing(processing)

  # 取得した画像をサーバーに保存する
  dV.save_image(datas)

  # "sc_daily"テーブルの実行
  usDaily.tb_upsert_sc_daily(afDtlLink, dateKey, datas)

  # wordpress用のテーブルに反映
  toWp.upsert_wp_table(afDtlLink, dateKey, datas)

# 関数を実行
aresort_page_list()