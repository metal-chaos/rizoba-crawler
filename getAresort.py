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
homeUrl = settings.AR_HOME_URL
listUrl = "https://www.a-resort.jp/resort/ankens/search/?page="
dateKey = datetime.datetime.now().strftime('%Y-%m-%d')

def get_work_info(detailSoup, kindOfElement):
  """Get information from 'お仕事詳細情報'

  Args:
    detailSoup (str): URL of a job detail page
    kindOfElement (str): Title of the job
  """

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

def get_treatment_info(detailSoup, kindOfElement):
  """Get information from '福利厚生'

  Args:
    detailSoup (str): URL of a job detail page
    kindOfElement (str): Title of the job
  Returns:
    targetValue (str): description of welfare
  """

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

def get_meal_info(detailSoup):
  """Get information of '食事支給'
  ①「有」で数字が「1」の場合はTRUE
  ② 「有」で数字が「2」の場合かつ「備考」に「円」が含まれていない場合はTRUE
  ③それ以外はFALSE

  Args:
    detailSoup (str): URL of a job detail page
  """

  targetValue = "FALSE"
  headElement = "<th rowspan=\"([0-9]*?)\" scope=\"row\">食事支給<\/th>\s*?<td( class=\"text-center br_dot\")?( style=\"width: 30px;\")?>\s*?([\s\S]*?)\s*?<\/td>"
  addElement = "[\s\S]*?<td class=\"br_dot\">備考<\/td>\s*?<td colspan=\"[0-9]*?\">([\s\S]*?)<\/td>[\s\S]*?ネット環境"
  remarksElement = headElement + addElement

  # 取得
  headResult = re.search(headElement, detailSoup)
  remarksResult = re.search(remarksElement, detailSoup)

  if ((headResult.group(1).strip() == 1 and headResult.group(4).strip() == "有"
    or int(headResult.group(1).strip()) >= 2 and headResult.group(4).strip() == "有" and not ("円" in remarksResult.group(5).strip()))):
    return "TRUE"
  else:
    return "FALSE"

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

  # ------------------- 【開始】求人詳細の各要素をスクレイピング -------------------
  # タイトル
  datas['title'] = detailSoup.title.string

  # 勤務地
  datas['place'] = re.search(r"<th>勤務地<\/th>\s*<td>([\s\S]*?)<\/td>", str(detailSoup))[1]

  # 職種
  datas['occupation'] = re.search(r"<h3>([\s\S]*?)<\/h3>", str(detailSoup))[1]

  # 勤務期間
  datas['term'] = re.search(r"<th>期間<\/th>\s*<td>([\s\S]*?)<\/td>", str(detailSoup))[1]

  # 給与
  arSalary = re.search(r"<th>給与<\/th>\s*<td>([\s\S]*?)(円[\s\S]*?)<\/td>", str(detailSoup))
  # 給与の種類
  datas['kindOfSalary'] = "KindOfSalary無し"
  # 給与（数値）
  datas['numOfSalary'] = int(arSalary[1].replace(',', ""))
  # 給与（掲載用）
  datas['salary'] = "時給" + arSalary[1] + arSalary[2]

  # 個室
  datas['dormitory'] = "TRUE" if ("/assets/resort/pc/images/page/resort/view/kodawari_icon2.jpg" in str(detailSoup)) else "FALSE"

  # 画像
  arPicture = re.search(r"<div id=\"fv\">\s*<img[\s\S]*?src=\"([\s\S]*?)\"", str(detailSoup))
  datas['picture'] = homeUrl + arPicture[1]

  # 勤務時間
  datas['time'] = get_work_info(str(detailSoup), "勤務時間")

  # 待遇
  datas['treatment'] = get_treatment_info(str(detailSoup), "福利厚生")

 # 仕事内容
  datas['jobDesc'] = re.search(r"<th>仕事内容<\/th>\s*<td colspan=\"3\">([\s\S]*?)<\/td>", str(detailSoup))[1]

  # パーマリンク
  urlNum = re.search(r"(\d+)", str(afDtlLink))
  datas['permaLink'] = "detail-alpha-" + str(urlNum[1])

  # 食事
  datas['meal'] = get_meal_info(str(detailSoup))

  # wifi
  datas['wifi'] = "TRUE" if ("/assets/resort/pc/images/page/resort/view/kodawari_icon8.jpg" in str(detailSoup)) else "FALSE"

  # 温泉
  datas['spa'] = "TRUE" if ("/assets/resort/pc/images/page/resort/view/kodawari_icon6.jpg" in str(detailSoup)) else "FALSE"

  # 交通費支給
  datas['transportationFee'] = "TRUE" if ("交通費支給" in str(detailSoup))  else "FALSE"

  # アフィリエイトリンク付与
  datas['affiliateLink'] = "https://px.a8.net/svt/ejp?a8mat=2HQA4W+4NAW2Y+39C6+BW8O2&a8ejpredirect=https%3A%2F%2Fwww.a-resort.jp%2Fresort%2Fankens%2Fview%2F%3Fid%3D" + str(urlNum[1])

  # キャンペーン
  datas['campaign'] = "TRUE"

  # 会社
  datas['company'] = "a-resort"
  # ------------------- 【終了】求人詳細の各要素をスクレイピング -------------------

  # 取得した画像をサーバーに保存する
  dV.save_image(datas)

  # "sc_daily"テーブルの実行
  usDaily.tb_upsert_sc_daily(afDtlLink, dateKey, datas)

  # wordpress用のテーブルに反映
  toWp.upsert_wp_table(afDtlLink, dateKey, datas)

# 関数を実行
aresort_page_list()