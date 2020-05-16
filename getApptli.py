# coding: UTF-8
import requests
import re
from bs4 import BeautifulSoup
from lxml import html
from time import sleep
import pymysql.cursors
import datetime
from distinct import distinctValue as dV
from processing import main, apptli
from upsert_mysql import sc_daily as usDaily
from upsert_mysql import refrectScDataToWp as toWp
from upsert_mysql import decidePrivatePublish as decidePP
import traceback,sys
import random
import settings

"""
Global variable
"""
apHomeUrl = settings.AP_HOME_URL
apListUrl = "https://hataraku.com/work/search/various/submit/?type=&page="
apDateKey = datetime.datetime.now().strftime('%Y-%m-%d')

def apptli_page_list():
  """
  Get information from job lists
  """

  apPNumber = 1

  while True:
    print("アプリ求人一覧「" + str(apPNumber) + "」ページ目の情報を取得中…")
    sleep(random.randint(1,8))

    try:
      apHtml = requests.get(apListUrl + str(apPNumber), timeout = 30)
      apSoup = BeautifulSoup(apHtml.text, 'html.parser')
    except:
      dV.exception_error_log()

    # 求人詳細へのリンクを全て取得
    apAllDtlLink = apSoup.select('section.vSubmitResultEach > a')
    for apEachDtlLink in apAllDtlLink:
      apBfDtlLink = re.search(r"(/work/detail\?work_id=\d+)", str(apEachDtlLink))
      apAfDtlLink = apHomeUrl + apBfDtlLink.group(0)
      try:
        apptli_page_detail(apAfDtlLink)
      except:
        dV.exception_error_log()

    # ページネーションから処理終了か判断
    if apSoup.find("a", class_="media-pagination-link is-next"):
      apPNumber += 1
    else:
      decidePP.decide_private_publish(apDateKey)
      break

# 求人詳細を取得
def apptli_page_detail(apAfDtlLink):
  """Get information from a job detail page

  Args:
    apDtlLink (str): URL of a job detail page
  """

  print("アプリ求人詳細「" + apAfDtlLink + "」の情報を取得中…")
  sleep(random.randint(1,8))

  apDetailHtml = requests.get(apAfDtlLink, timeout = 5)
  apDetailSoup = BeautifulSoup(apDetailHtml.text, 'html.parser')
  datas = {}

  # 求人詳細のスクレイピング
  processing = apptli.Apptli(apDetailSoup, apAfDtlLink)
  primary = main.Main()
  datas = primary.make_processing(processing)

  # 取得した画像をサーバーに保存する
  dV.save_image(datas)

  # "sc_daily"テーブルの実行
  usDaily.tb_upsert_sc_daily(apAfDtlLink, apDateKey, datas)

  # wordpress用のテーブルに反映
  toWp.upsert_wp_table(apAfDtlLink, apDateKey, datas)

# 関数を実行
apptli_page_list()