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

apHomeUrl = settings.AP_HOME_URL
apListUrl = "https://hataraku.com/work/search/various/submit/?type=&page="
apDateKey = datetime.datetime.now().strftime('%Y-%m-%d')

# （完）求人一覧を取得
def apptli_page_list(apDateKey):
  apPNumber = 1

  while True:
    print("アプリ求人一覧「" + str(apPNumber) + "」ページ目の情報を取得中…")
    sleep(random.randint(1,8))

    try:
      apHtml = requests.get(apListUrl + str(apPNumber), timeout = 30)
      apSoup = BeautifulSoup(apHtml.text, 'html.parser')
    except:
      dV.exception_error_log()

    # （完）求人詳細へのリンクを全て取得
    apAllDtlLink = apSoup.select('section.vSubmitResultEach > a')
    for apEachDtlLink in apAllDtlLink:
      apBfDtlLink = re.search(r"(/work/detail\?work_id=\d+)", str(apEachDtlLink))
      apAfDtlLink = apHomeUrl + apBfDtlLink.group(0)
      try:
        apptli_page_detail(apAfDtlLink, apDateKey)
      except:
        dV.exception_error_log()

    # （完）ページネーションから処理終了か判断
    if apSoup.find("a", class_="media-pagination-link is-next"):
      apPNumber += 1
    else:
      decidePP.decide_private_publish(apDateKey)
      break

# （完）求人詳細を取得
def apptli_page_detail(apAfDtlLink, apDateKey):
  print("アプリ求人詳細「" + apAfDtlLink + "」の情報を取得中…")
  sleep(random.randint(1,8))

  apDetailHtml = requests.get(apAfDtlLink, timeout = 5)
  apDetailSoup = BeautifulSoup(apDetailHtml.text, 'html.parser')

  # ------------------- 【開始】求人詳細の各要素をスクレイピング -------------------
  apTitle = apDetailSoup.title.string # タイトル
  apPlace = re.search(r"<span class=\"heading-list-txt_place\">\s*?<a href=\"[\s\S]*?\">([\s\S]*?)<\/a>\s*?<a href=\"[\s\S]*?\">([\s\S]*?)<\/a>", str(apDetailSoup)) # 勤務地
  apOccupation = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">職種<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">\s*?<a href=\"[\s\S]*?\">([\s\S]*?)<\/a>", str(apDetailSoup)) # 職種
  apTerm = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">期間<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", str(apDetailSoup)) # 勤務期間
  apSalary = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">(時給|日給|月給)<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)(円[\s\S]*?)<\/span>", str(apDetailSoup)) # 給与
  apDormitory = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">寮<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", str(apDetailSoup)) # 個室
  if ("個室" in apDormitory[1]):
    apDormitory = "TRUE"
  else:
    apDormitory = "FALSE"
  apPicture = re.search(r"<div class=\"list carousel-item\"><img[\s\S]*?src=\"([\s\S]*?)\"", str(apDetailSoup)) # 画像
  apTime = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">勤務時間<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", str(apDetailSoup)) # 勤務期間
  apTreatment = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">待遇<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", str(apDetailSoup)) # 待遇
  apJobDesc = re.search(r"<span class=\"detailJobContent__txt\">([\s\S]*?)<\/span>", str(apDetailSoup)) # 仕事内容
  # resorn用のパーマリンク作成
  apUrlNum = re.search(r"(\d+)", str(apAfDtlLink))
  apPermaLink = "detail-apptli-" + str(apUrlNum[1])
  # 食事
  if re.search(r"<span class=\"detailJobSummaryList__descTxt\">[\s\S]*?食事無料[\s\S]*?<div class=\"detailJobDetailOuter\">", str(apDetailSoup)):
    apMeal = "TRUE"
  else:
    apMeal = "FALSE"
  # wifi
  if ("<span class=\"detailJobTraitList__txt\">ネット利用可</span>" in str(apDetailSoup)):
    apWifi = "TRUE"
  else:
    apWifi = "FALSE"
  # 温泉
  if ("<span class=\"detailJobTraitList__txt\">温泉利用可</span>" in str(apDetailSoup)):
    apSpa = "TRUE"
  else:
    apSpa = "FALSE"
  # 交通費支給
  if re.search(r"<span class=\"detailJobSummaryList__descTxt\">[\s\S]*?光熱費無料[\s\S]*?<div class=\"detailJobDetailOuter\">", str(apDetailSoup)):
    apTransportationFee = "TRUE"
  else:
    apTransportationFee = "FALSE"
  # アフィリエイトリンク付与
  apAffiliateLink = "https://px.a8.net/svt/ejp?a8mat=2TOVB0+BLYDRE+2Z94+BW8O2&a8ejpredirect=https%3A%2F%2Fhataraku.com%2Fwork%2Fdetail%2F%3Fwork_id%3D" + str(apUrlNum[1])
  # ------------------- 【終了】求人詳細の各要素をスクレイピング -------------------

  # -------------------- 【開始】取得した画像をサーバーに保存する --------------------
  dV.save_image("apptli", apHomeUrl + apPicture[1], apPermaLink)
  # -------------------- 【終了】取得した画像をサーバーに保存する --------------------

# "sc_daily"テーブルの実行
  usDaily.tb_upsert_sc_daily(apAfDtlLink, apTitle, apPermaLink, apDormitory, apHomeUrl + apPicture[1], apOccupation[1], apSalary[1], int(apSalary[2].replace(',', "")), apSalary[1] + apSalary[2] + apSalary[3], apTerm[1], apTime[1], apTreatment[1], apJobDesc[1], apMeal, apTransportationFee, apWifi, apSpa, apPlace[1] + " " + apPlace[2], apAffiliateLink, "TRUE", "apptli", apDateKey)

# wordpress用のテーブルに反映
  toWp.upsert_wp_table(apAfDtlLink, apTitle, apPermaLink, apDormitory, apHomeUrl + apPicture[1], apOccupation[1], apSalary[1], int(apSalary[2].replace(',', "")), apSalary[1] + apSalary[2] + apSalary[3], apTerm[1], apTime[1], apTreatment[1], apJobDesc[1], apMeal, apTransportationFee, apWifi, apSpa, apPlace[1] + " " + apPlace[2], apAffiliateLink, "TRUE", "apptli", apDateKey)
  
# 関数を実行
apptli_page_list(apDateKey)