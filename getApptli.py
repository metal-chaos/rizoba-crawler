# coding: UTF-8
import requests
import re
from bs4 import BeautifulSoup
from lxml import html
from time import sleep
import pymysql.cursors
import datetime
from distinct import distinctValue as dV
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

# 求人一覧を取得
def apptli_page_list():
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

  # ------------------- 【開始】求人詳細の各要素をスクレイピング -------------------
  # タイトル
  datas['title'] = apDetailSoup.title.string

  # 勤務地
  apPlace = re.search(r"<span class=\"heading-list-txt_place\">\s*?<a href=\"[\s\S]*?\">([\s\S]*?)<\/a>\s*?<a href=\"[\s\S]*?\">([\s\S]*?)<\/a>", str(apDetailSoup))
  datas['place'] = apPlace[1] + " " + apPlace[2]

  # 職種
  datas['occupation'] = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">職種<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">\s*?<a href=\"[\s\S]*?\">([\s\S]*?)<\/a>", str(apDetailSoup))[1]

  # 勤務期間
  datas['term'] = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">期間<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", str(apDetailSoup))[1]

  # 給与
  salary = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">(時給|日給|月給)<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)(円[\s\S]*?)<\/span>", str(apDetailSoup))
  # 給与の種類
  datas['kindOfSalary'] = salary[1]
  # 給与（数値）
  datas['numOfSalary'] = int(salary[2].replace(',', ""))
  # 給与（掲載用）
  datas['salary'] = salary[1] + salary[2] + salary[3]

  # 個室
  dormitory = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">寮<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", str(apDetailSoup))
  datas['dormitory'] = "TRUE" if ("個室" in dormitory[1]) else "FALSE"

  # 画像
  picture = re.search(r"<div class=\"list carousel-item\"><img[\s\S]*?src=\"([\s\S]*?)\"", str(apDetailSoup))
  datas['picture'] = apHomeUrl + picture[1]

  # 勤務時間
  datas['time'] = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">勤務時間<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", str(apDetailSoup))[1]

  # 待遇
  datas['treatment'] = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">待遇<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", str(apDetailSoup))[1]

  # 仕事内容
  datas['jobDesc'] = re.search(r"<span class=\"detailJobContent__txt\">([\s\S]*?)<\/span>", str(apDetailSoup))[1]

  # パーマリンク
  apUrlNum = re.search(r"(\d+)", str(apAfDtlLink))
  datas['permaLink'] = "detail-apptli-" + str(apUrlNum[1])

  # 食事
  datas['meal'] = "TRUE" if re.search(r"<span class=\"detailJobSummaryList__descTxt\">[\s\S]*?食事無料[\s\S]*?<div class=\"detailJobDetailOuter\">", str(apDetailSoup)) else "FALSE"

  # wifi
  datas['wifi'] = "TRUE" if ("<span class=\"detailJobTraitList__txt\">ネット利用可</span>" in str(apDetailSoup)) else "FALSE"

  # 温泉
  datas['spa'] = "TRUE" if ("<span class=\"detailJobTraitList__txt\">温泉利用可</span>" in str(apDetailSoup)) else "FALSE"

  # 交通費支給
  datas['transportationFee'] = "TRUE" if re.search(r"<span class=\"detailJobSummaryList__descTxt\">[\s\S]*?光熱費無料[\s\S]*?<div class=\"detailJobDetailOuter\">", str(apDetailSoup)) else "FALSE"

  # アフィリエイトリンク付与
  datas['affiliateLink'] = "https://hataraku.com/work/detail?work_id=" + str(apUrlNum[1])

  # キャンペーン
  datas['campaign'] = "TRUE"

  # 会社
  datas['company'] = "apptli"
  # ------------------- 【終了】求人詳細の各要素をスクレイピング -------------------

  # 取得した画像をサーバーに保存する
  dV.save_image(datas)

# "sc_daily"テーブルの実行
  usDaily.tb_upsert_sc_daily(apAfDtlLink, apDateKey, datas)

# wordpress用のテーブルに反映
  toWp.upsert_wp_table(apAfDtlLink, apDateKey, datas)

# 関数を実行
apptli_page_list()