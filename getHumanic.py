# coding: UTF-8
import requests
import re
from bs4 import BeautifulSoup
from lxml import html
from time import sleep
import pymysql.cursors
import datetime
from distinct import distinctValue as dV
from processing import main, humanic
from upsert_mysql import sc_daily as usDaily
from upsert_mysql import refrectScDataToWp as toWp
from upsert_mysql import decidePrivatePublish as decidePP
import traceback,sys
import random
import settings

"""
Global variable
"""
homeUrl = settings.HU_HOME_URL
listUrl = "https://www.rizoba.com/search/result/?page="
dateKey = datetime.datetime.now().strftime('%Y-%m-%d')

def humanic_page_list():
  """
  Get information from job lists
  """

  pNumber = 1

  while True:
    print("ヒューマニック求人一覧「" + str(pNumber) + "」の情報を取得中…")
    sleep(random.randint(1,8))

    try:
      html = requests.get(listUrl + str(pNumber), timeout = 30)
      soup = BeautifulSoup(html.text, 'html.parser')
    except:
      dV.exception_error_log()

    # 求人詳細へのリンクを全て取得
    allDtlLink = soup.findAll("a", class_ = "button_ellipse skin_blue link_hover_opacity ga_link_event")
    for eachDtlLink in allDtlLink:
      bfDtlLink = re.search(r"(/work/\d+/)", str(eachDtlLink))
      afDtlLink = homeUrl + bfDtlLink.group(0)

      # 求人詳細の実行
      try:
        humanic_page_detail(afDtlLink)
      except:
        dV.exception_error_log()

    # ページネーションから処理終了か判断、item_page_linkへのリンクを全て取得
    if soup.find("li", class_ = "item_page skin_arrow_next"):
      pNumber += 1
    else:
      decidePP.decide_private_publish(dateKey)
      break

def humanic_page_detail(afDtlLink):
  """Get information from a job detail page

  Args:
    afDtlLink (str): URL of a job detail page
  """

  print("ヒューマニック求人詳細「" + afDtlLink + "」の情報を取得中…")
  sleep(random.randint(1,8))

  detailHtml = requests.get(afDtlLink, timeout = 5)
  detailSoup = BeautifulSoup(detailHtml.text, 'html.parser')
  datas = {}

  # 求人詳細のスクレイピング
  processing = humanic.Humanic(detailSoup, afDtlLink)
  primary = main.Main()
  datas = primary.make_processing(processing)

  # 取得した画像をサーバーに保存する
  dV.save_image(datas)

  # "sc_daily"テーブルの実行
  usDaily.tb_upsert_sc_daily(afDtlLink, dateKey, datas)

  # wordpress用のテーブルに反映
  toWp.upsert_wp_table(afDtlLink, dateKey, datas)

# 関数を実行
humanic_page_list()