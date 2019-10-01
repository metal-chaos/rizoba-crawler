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

arHomeUrl = settings.AR_HOME_URL
arListUrl = "https://www.a-resort.jp/resort/ankens/search/?page="
arDateKey = datetime.datetime.now().strftime('%Y-%m-%d')

###########################
# 概要: 「お仕事詳細情報」テーブルの中身を取得
# detailSoup: ページ全体のデータ
# kindOfElement: 仕事内容のタイトル
# targetValue: 仕事内容の中身
###########################
def get_work_info(detailSoup, kindOfElement):
    # 勤務時間があるか検索
    targetValue = ""
    headElement = "<tr>\s*?<th rowspan=\"([0-9]*?)\" scope=\"row\">" + kindOfElement + "<\/th>\s*?<td (class=)?([\s\S]*?)colspan=\"[0-9]*?\">\s*?([\s\S]*?)<\/td>\s*?<\/tr>"
    addElement = "\s*?<tr>\s*?<td (class=)?([\s\S]*?)colspan=\"[0-9]*?\">\s*?([\s\S]*?)<\/td>\s*?<\/tr>"
    getDataElement = "<td [class=]?[\s\S]*colspan=\"[0-9]*\">\s*([\s\S]*)<\/td>"
    newLine = "[\s\S]*"
    result = re.search(r"<tr>\s*?<th rowspan=\"([0-9]*?)\" scope=\"row\">" + kindOfElement + r"<\/th>\s*?<td (class=)?([\s\S]*?)colspan=\"[0-9]*?\">\s*?([\s\S]*?)<\/td>\s*?<\/tr>", detailSoup)

    if (result):
      addCountForHead = addCountForData = addCountForValue = int(result[1]) - 1
      entireElement = headElement
      getAllDataElement = getDataElement

      # （rowspanの数-1）分の正規表現を足す
      while addCountForHead > 0:
        addCountForHead += -1
        entireElement += addElement

      # 仕事内容の中身を取得
      getArrayValues = re.search(r"" + entireElement + r"", detailSoup)
      getValue = getArrayValues[0]

      # （rowspanの数-1）分の正規表現を足す
      while addCountForData > 0:
        addCountForData += -1
        getAllDataElement += newLine + getDataElement
      dataValues = re.search(r"" + getAllDataElement + r"", getValue)

      targetValue = dataValues.group(1)
      # （rowspanの数-1）分のマッチオブジェクトがあれば<br>で繋ぐ
      if (addCountForValue > 0):
        while addCountForValue > 0:
          targetValue += "<br>" + dataValues.group(addCountForValue + 1)
          addCountForValue += -1
    return targetValue

###########################
# 概要: 「福利厚生」テーブルの中身を取得（汎用性あり）
###########################
def get_treatment_info(detailSoup, kindOfElement):
  targetValue = ""
  elementName = []
  # 引数により取得するthの名前を変更
  if (kindOfElement == "福利厚生"):
    elementNames = ["交通費", "社会保険", "特典"]
  # searchして取得した各属性をtargetValueに格納
  for elementName in elementNames:
    getElement = r"<th scope=\"row\">" + elementName + r"<\/th>\s*?<td>\s*?([\s\S]*?)<\/td>"
    result = re.search(getElement, detailSoup)
    if (result):
      targetValue += elementName + "：" + result.group(1)
  return targetValue

# 求人一覧を取得
def aresort_page_list(arDateKey):
  arPNumber = 1

  while True:
    if arPNumber == 11 or arPNumber == 31:
      arPNumber += 3
    print("アルファ求人一覧「" + str(arPNumber) + "」ページ目の情報を取得中…")
    sleep(random.randint(1,8))

    try:
      arHtml = requests.get(arListUrl + str(arPNumber), timeout = 30)
      arSoup = BeautifulSoup(arHtml.text, 'html.parser')
    except:
      dV.exception_error_log()

    # 求人詳細へのリンクを全て取得
    arAllDtlLink = arSoup.select('div.works_list_link > a')
    for arEachDtlLink in arAllDtlLink:
      arBfDtlLink = re.search(r"(\/resort\/ankens\/view/\?id=\d+)", str(arEachDtlLink))
      arAfDtlLink = arHomeUrl + arBfDtlLink.group(0)
      # 求人詳細の実行
      try:
        aresort_page_detail(arAfDtlLink, arDateKey)
      except:
        dV.exception_error_log()

    # ページネーションから処理終了か判断、item_page_linkへのリンクを全て取得
    if arPNumber == 1:
      arPNumber += 1
    else:
      forReLink = arSoup.findAll("a", title= "Last")[1].text.translate(str.maketrans({"[": None, "]": None})) # 最後の番号を取得
      if int(forReLink) > arPNumber:
        arPNumber += 1
      else:
        decidePP.decide_private_publish(arDateKey)
        break

# 求人詳細を取得
def aresort_page_detail(arAfDtlLink, arDateKey):
  print("アルファ求人詳細「" + arAfDtlLink + "」の情報を取得中…")
  sleep(random.randint(1,8))

  arDetailHtml = requests.get(arAfDtlLink, timeout = 5)
  arDetailSoup = BeautifulSoup(arDetailHtml.text, 'html.parser')
  getWorkInfo = get_work_info
  getTreatmentInfo = get_treatment_info

  # ------------------- 【開始】求人詳細の各要素をスクレイピング -------------------
  arTitle = arDetailSoup.title.string # タイトル
  arPlace = re.search(r"<th>勤務地<\/th>\s*<td>([\s\S]*?)<\/td>", str(arDetailSoup)) # 勤務地
  arOccupation = re.search(r"<h3>([\s\S]*?)<\/h3>", str(arDetailSoup)) # 職種
  arTerm = re.search(r"<th>期間<\/th>\s*<td>([\s\S]*?)<\/td>", str(arDetailSoup)) # 勤務期間
  arSalary = re.search(r"<th>給与<\/th>\s*<td>([\s\S]*?)(円[\s\S]*?)<\/td>", str(arDetailSoup)) # 給与
  if (".dqQ3_nx2-_" in str(arDetailSoup)): # 個室
    arDormitory = "TRUE"
  else:
    arDormitory = "FALSE"
  arPicture = re.search(r"<div id=\"fv\">\s*<img[\s\S]*?src=\"([\s\S]*?)\"", str(arDetailSoup)) # 画像
  arTime = getWorkInfo(str(arDetailSoup), "勤務時間") # 勤務時間
  print("勤務時間は" + arTime)
  arTreatment = getTreatmentInfo(str(arDetailSoup), "福利厚生") # 待遇
  print("待遇は" + arTreatment)
  arJobDesc = re.search(r"<th>仕事内容<\/th>\s*<td colspan=\"3\">([\s\S]*?)<\/td>", str(arDetailSoup)) # 仕事内容
  # resorn用のパーマリンク作成
  arUrlNum = re.search(r"(\d+)", str(arAfDtlLink))
  arPermaLink = "detail-alpha-" + str(arUrlNum[1])
  # 食事
  if (re.search(r"<th>食事<\/th>\s*<td>[\s\S]*?自己負担なし[\s\S]*?<\/td>", str(arDetailSoup))):
    arMeal = "TRUE"
  else:
    arMeal = "FALSE"
  # wifi
  if (re.search(r"<th>ネット環境<\/th>\s*<td>有<\/td>", str(arDetailSoup))):
    arWifi = "TRUE"
  else:
    arWifi = "FALSE"
  # 温泉
  if ("/assets/resort/pc/images/page/resort/view/kodawari_icon6.jpg" in str(arDetailSoup)):
    arSpa = "TRUE"
  else:
    arSpa = "FALSE"
  # 交通費支給
  if ("交通費支給" in str(arDetailSoup)):
    arTransportationFee = "TRUE"
  else:
    arTransportationFee = "FALSE"
  # アフィリエイトリンク付与
  arAffiliateLink = "https://px.a8.net/svt/ejp?a8mat=2HQA4W+4NAW2Y+39C6+BW8O2&a8ejpredirect=https%3A%2F%2Fwww.a-resort.jp%2Fresort%2Fankens%2Fview%2F%3Fid%3D" + str(arUrlNum[1])

  #print("福利厚生は" + arTreatment[1]) TODO:


  # ------------------- 【終了】求人詳細の各要素をスクレイピング -------------------

  # -------------------- 【開始】取得した画像をサーバーに保存する --------------------
  dV.save_image("a-resort", arHomeUrl + arPicture[1], arPermaLink)
  # -------------------- 【終了】取得した画像をサーバーに保存する --------------------



  # "sc_daily"テーブルの実行
  #usDaily.tb_upsert_sc_daily(arAfDtlLink, arTitle, arPermaLink, arDormitory, arHomeUrl + arPicture[1], arOccupation[1], "KindOfSalary無し", int(arSalary[1].replace(',', "")), "時給" + arSalary[1] + arSalary[2], arTerm[1], arTime[1], arTreatment[1], arJobDesc[1], arMeal, arTransportationFee, arWifi, arSpa, arPlace[1], arAffiliateLink, "TRUE", "a-resort", arDateKey)

  # "wordpress用のテーブルに反映"
  #toWp.upsert_wp_table(arAfDtlLink, arTitle, arPermaLink, arDormitory, arHomeUrl + arPicture[1], arOccupation[1], "KindOfSalary無し", int(arSalary[1].replace(',', "")), "時給" + arSalary[1] + arSalary[2], arTerm[1], arTime[1], arTreatment[1], arJobDesc[1], arMeal, arTransportationFee, arWifi, arSpa, arPlace[1], arAffiliateLink, "TRUE", "a-resort", arDateKey)


# 関数を実行
aresort_page_list(arDateKey)