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
homeUrl = settings.HU_HOME_URL
listUrl = "https://www.rizoba.com/search/result/?page="
huDateKey = datetime.datetime.now().strftime('%Y-%m-%d')

def humanic_page_list():
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
      decidePP.decide_private_publish(huDateKey)
      break

def humanic_page_detail(afDtlLink):
  """
  求人詳細を取得

  Parameters
  ----------
  afDtlLink : str
    求人詳細ページのURL
  """
  print("ヒューマニック求人詳細「" + afDtlLink + "」の情報を取得中…")
  sleep(random.randint(1,8))

  detailHtml = requests.get(afDtlLink, timeout = 5)
  detailSoup = BeautifulSoup(detailHtml.text, 'html.parser')
  datas = {}

  # ------------------- 【開始】求人詳細の各要素をスクレイピング -------------------
  # タイトル
  datas['title'] = detailSoup.title.string

  # 勤務地
  datas['place'] = re.search(r"<dt class=\"item_info_term\">\s*勤務地\s*<\/dt>\s*<dd class=\"item_info_description\">\s*(.*)\s*<\/dd>", str(detailSoup))[1]

  # 職種
  datas['occupation'] = re.search(r"<dt class=\"item_info_term\">\s*職種\s*<\/dt>\s*<dd class=\"item_info_description\">\s*(.*)\s*<\/dd>", str(detailSoup))[1]

  # 勤務期間
  datas['term'] = re.search(r"<dt class=\"item_info_term\">\s*期間\s*<\/dt>\s*<dd class=\"item_info_description\">\s*(.*)\s*<\/dd>", str(detailSoup))[1]

  # 給与
  salary = re.search(r"<dt class=\"item_info_term\">\s*(時給|日給|月給)\s*<\/dt>\s*<dd class=\"item_info_description\">\s*(.*)(円)\s*<\/dd>", str(detailSoup))
  # 給与の種類
  datas['kindOfSalary'] = salary[1]
  # 給与（数値）
  datas['numOfSalary'] = salary[2]
  # 給与（掲載用）
  datas['salary'] = salary[1] + salary[2] + "円"

  # 個室
  dormitory = re.search(r"<dt class=\"item_info_term\">\s*寮の種類\s*<\/dt>\s*<dd class=\"item_info_description\">\s*(.*)\s*<\/dd>", str(detailSoup))
  datas['dormitory'] = "TRUE" if ("個室" in dormitory[1]) else "FALSE"

  # 画像
  datas['picture'] = re.search(r"<span class=\"item_slide_image\">\s*<img alt=\"[\s\S]*?\" src=\"([\s\S]*?)\"", str(detailSoup))[1]

  # 勤務時間
  datas['time'] = re.search(r"<dd class=\"item_info_description work_time_unit\">\s*([\s\S]*?)\s*<\/dd>", str(detailSoup))[1]

  # 待遇
  datas['treatment'] = re.search(r"<dt class=\"item_info_term\">\s*福利厚生\s*<\/dt>\s*<dd class=\"item_info_description\">\s*([\s\S]*?)\s*<\/dd>", str(detailSoup))[1]

  # 仕事内容
  datas['jobDesc'] = re.search(r"<dt class=\"item_info_lead_term\">\s*仕事内容\s*<\/dt>\s*<dd class=\"item_info_lead_description\">\s*([\s\S]*?)\s*<\/dd>", str(detailSoup))[1]

  # パーマリンク
  urlNum = re.search(r"(\d+)", str(afDtlLink))
  datas['permaLink'] = "detail-humanic-" + str(urlNum[1])

  # 食事
  datas['meal'] = "TRUE" if ("食費無料" in str(detailSoup)) else "FALSE"

  # wifi
  datas['wifi'] = "TRUE" if ("食費無料" in str(detailSoup)) else "FALSE"

  # 温泉
  datas['spa'] = "TRUE" if ("item_merit skin_merit_m2_16" in str(detailSoup)) else "FALSE"

  # 交通費支給
  datas['transportationFee'] = "TRUE" if ("交通費支給" in str(detailSoup)) else "FALSE"

  # アフィリエイトリンク付与
  datas['affiliateLink'] = "https://px.a8.net/svt/ejp?a8mat=2ZJJHC+5VYEGA+42GS+BW8O2&a8ejpredirect=https%3A%2F%2Fwww.rizoba.com%2Fwork%2F" + str(urlNum[1]) + "%2F"

  # キャンペーン
  datas['campaign'] = "FALSE"

  # 会社
  datas['company'] = "humanic"
  # ------------------- 【終了】求人詳細の各要素をスクレイピング -------------------

  # 取得した画像をサーバーに保存する
  dV.save_image(datas)

  # "sc_daily"テーブルの実行
  usDaily.tb_upsert_sc_daily(afDtlLink, huDateKey, datas)

  # wordpress用のテーブルに反映
  toWp.upsert_wp_table(afDtlLink, huDateKey, datas)

# 関数を実行
humanic_page_list()