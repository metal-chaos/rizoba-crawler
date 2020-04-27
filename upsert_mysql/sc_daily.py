# coding: UTF-8
from distinct import distinctValue as dV
import datetime
import connection

def tb_upsert_sc_daily(dtlLink, dateKey, datas):
  """Upsert values into 'sc_daily' table

  Args:
    dtlLink (str): URL of a job detail page
    dateKey (str): The day that started crawling
    datas (array): Datas that have already crawled and getted
  """
  mysqlConnect = connection.connect()
  conn = mysqlConnect.connect_mysql()
  cur = conn.cursor()

  # 現在の日時を取得
  now = datetime.datetime.now()

  try:
    with cur as cursor:
      # post_categoryの判別処理
      categorySlug = dV.post_category(cur, datas['place'], cursor)
      # occupacion_tagsの判別処理
      occupationSlug = dV.distinct_occupation_tags(cur, datas['occupation'], cursor)
      # tax_salaryの判別処理
      taxSalary = dV.distinct_tax_salary(datas['kindOfSalary'], int(datas['numOfSalary']))
      # icon_highincome_fieldの判別処理
      iconHighIncome = dV.distinct_icon_highincome_field(taxSalary)
      # menu_orderの値の判別処理（あとで変更したい）
      menuOrder = dV.distinct_menu_order()
      # MySQLへのINSERT INTO処理
      sql = "INSERT INTO sc_daily \
      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
      ON DUPLICATE KEY UPDATE sc_date = %s, date_key = %s, post_title = %s, post_excerpt = %s, menu_order = %s, post_thumbnail = %s, post_category = %s, occupation_tags = %s, tax_salary = %s, icon_dormitory_field = %s, icon_highIncome_field = %s, icon_campaign_field = %s, company_field = %s, occupation_field = %s, salary_field = %s, term_field = %s, time_field = %s, treatment_field = %s, jobDescription_field = %s, affiliatelink_field = %s, icon_meal_field = %s, icon_transportationFee_field = %s, icon_wifi_field = %s, icon_spa_field = %s"
      cursor.execute(sql, ("",
        now,
        dtlLink,
        dateKey,
        datas['title'],
        datas['jobDesc'],
        datas['permaLink'],
        menuOrder,
        datas['picture'],
        categorySlug,
        occupationSlug,
        taxSalary,
        datas['dormitory'],
        iconHighIncome,
        datas['campaign'],
        datas['company'],
        datas['occupation'],
        datas['salary'],
        datas['term'],
        datas['time'],
        datas['treatment'],
        datas['jobDesc'],
        datas['affiliateLink'],
        datas['meal'],
        datas['transportationFee'],
        datas['wifi'],
        datas['spa'],
        now,
        dateKey,
        datas['title'],
        datas['jobDesc'],
        menuOrder,
        datas['picture'],
        categorySlug,
        occupationSlug,
        taxSalary,
        datas['dormitory'],
        iconHighIncome,
        datas['campaign'],
        datas['company'],
        datas['occupation'],
        datas['salary'],
        datas['term'],
        datas['time'],
        datas['treatment'],
        datas['jobDesc'],
        datas['affiliateLink'],
        datas['meal'],
        datas['transportationFee'],
        datas['wifi'],
        datas['spa']
      ))

    # オートコミットじゃないので、明示的にコミットを書く必要がある
    conn.commit()
  finally:
    conn.close()
