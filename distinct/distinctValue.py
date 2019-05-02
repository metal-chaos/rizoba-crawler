# coding: UTF-8
import requests
import random
import re
import pymysql.cursors
import traceback,sys

# -----------------------------------
# 概要：tax_salaryタグを判別するメソッド
# -----------------------------------
def distinct_tax_salary(KindOfSalary, figureOfsalary):
  if "日給" in KindOfSalary or "月給" in KindOfSalary:
    return("monthly")
  elif figureOfsalary is None:
    return("")
  elif figureOfsalary <= 800:
    return("800")
  elif 800 < figureOfsalary and figureOfsalary <= 900:
    return("801-900")
  elif 900 < figureOfsalary and figureOfsalary <= 1000:
    return("901-1000")
  elif 1000 < figureOfsalary and figureOfsalary <= 1100:
    return("1001-1100")
  elif 1100 < figureOfsalary and figureOfsalary <= 1200:
    return("1101-1200")
  elif 1200 < figureOfsalary and figureOfsalary <= 1300:
    return("1201-1300")
  elif 1300 < figureOfsalary and figureOfsalary <= 1400:
    return("1301-1400")
  else:
    return("1401")

# -----------------------------------
# 概要：時給が高いかどうかを判断するメソッド
# -----------------------------------
def distinct_icon_highincome_field(whetherHi):
  if whetherHi == "1201-1300" or whetherHi == "1301-1400" or whetherHi == "1401":
    return("TRUE")
  else:
    return("FALSE")

# -----------------------------------
# 概要：職種を判断するメソッド
# -----------------------------------
def distinct_occupation_tags(cur, scrapedOccuName, cursor):
  sql = "SELECT * FROM sc_occupations"
  cursor.execute(sql)
  values = cursor.fetchall()
  for value in values:
    occuName = str(value['occupation_name'])
    occuSlug = str(value['occupation_slug'])
    if occuName in scrapedOccuName:
      return(occuSlug)
  return("other-job")

# -----------------------------------
# 概要：ランダムに数値を生成するメソッド
# -----------------------------------
def distinct_menu_order():
  index = random.randint(1,200000)
  return(index)

# -----------------------------------
# 概要：エリアのスラッグを判断するメソッド
# -----------------------------------
def post_category(cur, prefecturesAllName, cursor):
  separatedArea = re.search(r"((京都|[\S]*?)(都|道|府|県|市)\s*([\S]*))", str(prefecturesAllName))
  sql = "SELECT prefectures_detail_slug FROM sc_preferctures_detail WHERE prefectures_detail_name = %s"
  cursor.execute(sql, (separatedArea[4]))
  value = cursor.fetchone()
  # ①子エリアのスラッグがないか検索する処理
  if value != None:
    areaSlug = str(value['prefectures_detail_slug'])
  # ②北海道エリアのスラッグがないか検索する処理
  elif separatedArea[2] == "北海":
    sql = "SELECT prefectures_slug FROM sc_preferctures WHERE prefectures_name = %s"
    cursor.execute(sql, (separatedArea[2] + separatedArea[3]))
    value = cursor.fetchone()
    areaSlug = str(value['prefectures_slug'])
  # ③親エリアのスラッグがないか検索する処理
  else:
    sql = "SELECT prefectures_slug FROM sc_preferctures WHERE prefectures_name = %s"
    cursor.execute(sql, (separatedArea[2]))
    value = cursor.fetchone()
    areaSlug = str(value['prefectures_slug'])
  return(areaSlug)

# -----------------------------------
# 概要：エラーログを吐き出すメソッド
# -----------------------------------
def exception_error_log():
  ex, ms, tb = sys.exc_info()
  print("\nex -> \t",type(ex))
  print(ex)
  print("\nms -> \t",type(ms))
  print(ms)
  print("\ntb -> \t",type(tb))
  print(tb)
  print("\n=== and print_tb ===")
  traceback.print_tb(tb)

# -----------------------------------
# 概要：取得した画像を指定のディレクトリに保存するメソッド
# -----------------------------------
def save_image(companyName, companyPicturePath, picturePermaLink):
  saveImagePath = "/home/komuinresign/resorn.net/public_html/wp-content/uploads/crawled-images/" + companyName + "/" + picturePermaLink + ".jpg"
  reImage = requests.get(companyPicturePath)
  with open(saveImagePath, mode = "wb") as f:
    f.write(reImage.content)

# -----------------------------------
# 概要：RESORNスコアを算出するメソッド
# -----------------------------------
def resorn_score(dormitory, campaign, meal, transportationFee, wifi, spa, KindOfSalary, figureOfsalary):
  print(dormitory)
  print(campaign)
  print(meal)
  print(transportationFee)
  print(wifi)
  print(spa)
  print(KindOfSalary)
  print(figureOfsalary)
  sum_resorn_score = 0
  welfares = [dormitory, campaign, meal, transportationFee, wifi, spa]
  for welfare in welfares:
    if welfare == "TRUE":
      sum_resorn_score += 0.5
  if "日給" in KindOfSalary or "月給" in KindOfSalary:
    return sum_resorn_score
  else:
    if 900 <= figureOfsalary and figureOfsalary < 1000:
      sum_resorn_score += 0.5
    elif 1000 <= figureOfsalary and figureOfsalary < 1100:
      sum_resorn_score += 1
    elif 1100 <= figureOfsalary and figureOfsalary < 1200:
      sum_resorn_score += 1.5
    elif 1200 <= figureOfsalary:
      sum_resorn_score += 2
    print(sum_resorn_score)
    return sum_resorn_score