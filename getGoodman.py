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

gdHomeUrl = "https://www.resortbaito.com/"
gdListUrl1 = "https://www.resortbaito.com/search-results/?area="
gdListUrl2 = "&extra=&top=on"
gdDateKey = datetime.datetime.now().strftime('%Y-%m-%d')

# （完）求人一覧を取得
def goodman_page_list(gdDateKey):

  gdAreaLists = ['hokkaido', 'tohoku', 'kanto', 'hokuriku', 'tokai', 'kansai', 'chugoku', 'kyushu', 'okinawa']
  for gdAreaList in gdAreaLists:
    print("グッドマン求人一覧「" + gdAreaList + "」の情報を取得中…")
    sleep(random.randint(1,8))

    try:
      gdHtml = requests.get(gdListUrl1 + gdAreaList + gdListUrl2, timeout = 30)
      gdSoup = BeautifulSoup(gdHtml.text, 'html.parser')
    except:
      dV.exception_error_log()

    gdAllDtlLink = gdSoup.select('ul.list-baito > li > a')
    for gdEachDtlLink in gdAllDtlLink:
      gdAfDtlLink = re.search(r"(a href=\"(https:\/\/www\.resortbaito\.com\/\d+\/)\")", str(gdEachDtlLink))
      try:
        goodman_page_detail(gdAfDtlLink, gdDateKey) # 求人詳細実行
      except:
        dV.exception_error_log()
  decidePP.decide_private_publish(gdDateKey)

# （完）求人詳細を取得
def goodman_page_detail(gdAfDtlLink, gdDateKey):
  print("グッドマン求人詳細「" + str(gdAfDtlLink[2]) + "」の情報を取得中…")
  sleep(random.randint(1,8))

  gdDetailHtml = requests.get(gdAfDtlLink[2], timeout = 5)
  gdDetailSoup = BeautifulSoup(gdDetailHtml.text, 'html.parser')

  # ------------------- 【開始】求人詳細の各要素をスクレイピング -------------------
  gdTitle = gdDetailSoup.title.string # タイトル
  gdPlace = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>勤務地<\/dt>[\s\S]*?<dd>([\s\S]*?)・([\s\S]*?)<\/dd>", str(gdDetailSoup)) # 勤務地
  gdOccupation = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>職種<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(gdDetailSoup)) # 職種
  gdTerm = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>働く期間<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(gdDetailSoup)) # 働く期間
  gdSalary = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>給与<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(gdDetailSoup)) # 給与
  gdSalaryFigure = re.search(r"[\s\S]*?(\d+)[\s\S]*?", str(gdSalary[1].replace(',', "")))
  # ---------------- 【補足】 ----------------
  # ①時給とか入ってるやつ：gdSalary[1]で対応可能
  # ②数値：re.searchかな
  # ③全て：gdSalary[1]で対応可能
  # -----------------------------------------
  # 個室
  if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op09\.png\"\/>", str(gdDetailSoup))):
    gdDormitory = "TRUE"
  else:
    gdDormitory = "FALSE"
  gdPicture = re.search(r"<div class=\"photo\">\s*<img[\s\S]*?src=\"([\s\S]*?)\"", str(gdDetailSoup)) # 画像
  gdTime = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>勤務時間<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(gdDetailSoup)) # 勤務時間
  gdTreatment = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>待遇<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(gdDetailSoup)) # 待遇
  gdJobDesc = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>仕事内容<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", str(gdDetailSoup)) # 仕事内容
  # resorn用のパーマリンク作成
  gdUrlNum = re.search(r"(\d+)", str(gdAfDtlLink[2]))
  gdPermaLink = "detail-goodman-" + str(gdUrlNum[1])
  # 食事
  if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op05\.png\"\/>", str(gdDetailSoup))):
    gdMeal = "TRUE"
  else:
    gdMeal = "FALSE"
  # wifi
  if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op22\.png\"\/>", str(gdDetailSoup))):
    gdWifi = "TRUE"
  else:
    gdWifi = "FALSE"
  # 温泉
  if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op19\.png\"\/>", str(gdDetailSoup))):
    gdSpa = "TRUE"
  else:
    gdSpa = "FALSE"
  # 交通費支給
  if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op07\.png\"\/>", str(gdDetailSoup))):
    gdTransportationFee = "TRUE"
  else:
    gdTransportationFee = "FALSE"
  # アフィリエイトリンク付与
  gdAffiliateLink = "https://px.a8.net/svt/ejp?a8mat=2TOVB0+BE7QWA+3OHQ+BW8O2&a8ejpredirect=http%3A%2F%2Fwww.resortbaito.com%2F" + str(gdUrlNum[1])
  # ------------------- 【終了】求人詳細の各要素をスクレイピング -------------------

  # -------------------- 【開始】取得した画像をサーバーに保存する --------------------
  dV.save_image("goodman", gdPicture[1], gdPermaLink)
  # -------------------- 【終了】取得した画像をサーバーに保存する --------------------

  # "sc_daily"テーブルの実行
  usDaily.tb_upsert_sc_daily(gdAfDtlLink[2], gdTitle, gdPermaLink, gdDormitory, gdPicture[1], gdOccupation[1], gdSalary[1], gdSalaryFigure[1], gdSalary[1], gdTerm[1], gdTime[1], gdTreatment[1], gdJobDesc[1], gdMeal, gdTransportationFee, gdWifi, gdSpa, gdPlace[1] + " " + gdPlace[2], gdAffiliateLink, "TRUE", "goodman", gdDateKey)

  # wordpress用のテーブルに反映
  toWp.upsert_wp_table(gdAfDtlLink[2], gdTitle, gdPermaLink, gdDormitory, gdPicture[1], gdOccupation[1], gdSalary[1], gdSalaryFigure[1], gdSalary[1], gdTerm[1], gdTime[1], gdTreatment[1], gdJobDesc[1], gdMeal, gdTransportationFee, gdWifi, gdSpa, gdPlace[1] + " " + gdPlace[2], gdAffiliateLink, "TRUE", "goodman", gdDateKey)
  
# 関数を実行
goodman_page_list(gdDateKey)