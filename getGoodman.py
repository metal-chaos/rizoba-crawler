# coding: UTF-8
import requests
import re
from bs4 import BeautifulSoup
from lxml import html
from time import sleep
import pymysql.cursors
import datetime
from distinct import distinctValue as dV
from processing import main, goodman
from upsert_mysql import sc_daily as usDaily
from upsert_mysql import refrectScDataToWp as toWp
from upsert_mysql import decidePrivatePublish as decidePP
import traceback,sys
import random
import settings

listUrl1 = "https://www.resortbaito.com/search-results/?area="
listUrl2 = "&extra=&top=on"
dateKey = datetime.datetime.now().strftime('%Y-%m-%d')

def goodman_page_list():
  """
  Get information from job lists
  """

  areaLists = ['hokkaido', 'tohoku', 'kanto', 'hokuriku', 'tokai', 'kansai', 'chugoku', 'kyushu', 'okinawa']
  for areaList in areaLists:
    print("グッドマン求人一覧「" + areaList + "」の情報を取得中…")
    sleep(random.randint(1,8))

    try:
      gdHtml = requests.get(listUrl1 + areaList + listUrl2, timeout = 30)
      gdSoup = BeautifulSoup(gdHtml.text, 'html.parser')
    except:
      dV.exception_error_log()

    allDtlLink = gdSoup.select('ul.list-baito > li > a')
    for eachDtlLink in allDtlLink:
      afDtlLink = re.search(r"(a href=\"(https:\/\/www\.resortbaito\.com\/\d+\/)\")", str(eachDtlLink))[2]
      try:
        goodman_page_detail(afDtlLink) # 求人詳細実行
      except:
        dV.exception_error_log()
  decidePP.decide_private_publish(dateKey)

def goodman_page_detail(afDtlLink):
  """Get information from detail pages

  Args:
    afDtlLink (str): URL of a job detail page
  """

  print("グッドマン求人詳細「" + str(afDtlLink) + "」の情報を取得中…")
  sleep(random.randint(1,8))

  detailHtml = requests.get(afDtlLink, timeout = 5)
  detailSoup = BeautifulSoup(detailHtml.text, 'html.parser')
  datas = {}

  # 求人詳細のスクレイピング
  processing = goodman.Goodman(detailSoup, afDtlLink)
  primary = main.Main()
  datas = primary.make_processing(processing)

  # 取得した画像をサーバーに保存する
  dV.save_image(datas)

  # "sc_daily"テーブルの実行
  usDaily.tb_upsert_sc_daily(afDtlLink, dateKey, datas)

  # wordpress用のテーブルに反映
  toWp.upsert_wp_table(afDtlLink, dateKey, datas)

# 関数を実行
goodman_page_list()