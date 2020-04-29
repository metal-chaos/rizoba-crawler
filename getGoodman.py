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

  # ------------------- 【開始】求人詳細の各要素をスクレイピング -------------------
  # タイトル
  datas['title'] = detailSoup.title.string

  # 勤務地
  gdPlace = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>勤務地<\/dt>[\s\S]*?<dd>([\s\S]*?)・([\s\S]*?)<\/dd>", str(detailSoup))
  datas['place'] = gdPlace[1] + " " + gdPlace[2]

  # 職種
  datas['occupation'] = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>職種<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(detailSoup))[1]

  # 働く期間
  datas['term'] = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>働く期間<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(detailSoup))[1]

  # 給与
  salary = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>給与<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(detailSoup))
  salaryFigure = re.search(r"[\s\S]*?(\d+)[\s\S]*?", str(salary[1].replace(',', "")))
  # 給与の種類
  datas['kindOfSalary'] = salary[1]
  # 給与（数値）
  datas['numOfSalary'] = salaryFigure[1]
  # 給与（掲載用）
  datas['salary'] = salary[1]

  # 個室
  datas['dormitory'] = "TRUE" if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op09\.png\"\/>", str(detailSoup))) else "FALSE"

  # 画像
  datas['picture'] = re.search(r"<div class=\"photo\">\s*<img[\s\S]*?src=\"([\s\S]*?)\"", str(detailSoup))[1]

  # 勤務時間
  datas['time'] = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>勤務時間<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(detailSoup))[1]

  # 待遇
  datas['treatment'] = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>待遇<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(detailSoup))[1]

  # 仕事内容
  datas['jobDesc'] = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>仕事内容<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(detailSoup))[1]

  # パーマリンク
  gdUrlNum = re.search(r"(\d+)", str(afDtlLink))
  datas['permaLink'] = "detail-goodman-" + str(gdUrlNum[1])

  # 食事
  datas['meal'] = "TRUE" if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op05\.png\"\/>", str(detailSoup))) else "FALSE"

  # wifi
  datas['wifi'] = "TRUE" if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op22\.png\"\/>", str(detailSoup))) else "FALSE"

  # 温泉
  datas['spa'] = "TRUE" if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op19\.png\"\/>", str(detailSoup))) else "FALSE"

  # 交通費支給
  datas['transportationFee'] = "TRUE" if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op07\.png\"\/>", str(detailSoup))) else "FALSE"

  # アフィリエイトリンク付与
  datas['affiliateLink'] = "https://px.a8.net/svt/ejp?a8mat=2TOVB0+BE7QWA+3OHQ+BW8O2&a8ejpredirect=http%3A%2F%2Fwww.resortbaito.com%2F" + str(gdUrlNum[1])

  # キャンペーン
  datas['campaign'] = "TRUE"

  # 会社
  datas['company'] = "goodman"
  # ------------------- 【終了】求人詳細の各要素をスクレイピング -------------------

  # 取得した画像をサーバーに保存する
  dV.save_image(datas)

  # "sc_daily"テーブルの実行
  usDaily.tb_upsert_sc_daily(afDtlLink, dateKey, datas)

  # wordpress用のテーブルに反映
  toWp.upsert_wp_table(afDtlLink, dateKey, datas)

# 関数を実行
goodman_page_list()