# coding: UTF-8
import traceback,sys
from time import sleep
import datetime
from distinct import distinctValue as dV
import connection
import settings

def upsert_wp_table(dtlLink, dateKey, datas):
  """Upsert values into for 'wordpress' table

  Args:
    dtlLink (str): URL of a job detail page
    dateKey (str): The day that started crawling
    datas (array): Datas that have already crawled and getted
  """
  mysqlConnect = connection.connect()
  conn = mysqlConnect.connect_mysql()
  cur = conn.cursor()

  # ------------------------------------------------
  # "sc_daily"テーブルからWordpress用のテーブルにupsert
  # ------------------------------------------------

  sleep(2)

  now = datetime.datetime.now()

  with cur as cursor:
    print("「" + datas['permaLink'] + "」の格納を開始…!")
    try:
      # post_categoryの判別処理
      upCategorySlug = dV.post_category(cur, datas['place'], cursor)
      # occupacion_tagsの判別処理
      occupationSlug = dV.distinct_occupation_tags(cur, datas['occupation'], cursor)
      # tax_salaryの判別処理
      upTaxSalary = dV.distinct_tax_salary(datas['kindOfSalary'], int(datas['numOfSalary']))
      # icon_highincome_fieldの判別処理
      upIconHighIncome = dV.distinct_icon_highincome_field(upTaxSalary)
      # menu_orderの値の判別処理（あとで変更したい）
      upMenuOrder = dV.distinct_menu_order()
      # RESORNスコア算出の処理
      upResornScore = dV.resorn_score(datas['dormitory'], datas['campaign'], datas['meal'], datas['transportationFee'], datas['wifi'], datas['spa'], datas['kindOfSalary'], int(datas['numOfSalary']))
      # int_salary_fieldの判別処理
      upIntSalaryField = dV.distinct_int_salary_field(datas['kindOfSalary'], int(datas['numOfSalary']))

      # ------------------------------------------------
      # ①"wp_posts"テーブルに求人情報をUPSERT
      # ------------------------------------------------
      # post_nameが存在するか確認する
      postsSql = "SELECT * FROM wp_posts WHERE post_name = %s"
      cursor.execute(postsSql, (datas['permaLink']))
      # post_nameが存在するならUPDATE
      if cursor.fetchone():
        postsSql = "UPDATE wp_posts SET post_content = %s, post_title = %s, post_excerpt = %s, menu_order = %s, post_modified = %s, post_modified_gmt = %s WHERE post_name = %s"
        cursor.execute(postsSql, ("[job_detail_text]", datas['title'], datas['jobDesc'], upMenuOrder, now, now, datas['permaLink']))
      # post_nameが存在しないならINSERT INTO
      else:
        postsSql = "INSERT INTO wp_posts (post_author, post_date, post_date_gmt, post_content, post_title, post_excerpt, comment_status, post_name, to_ping, pinged, post_modified, post_modified_gmt, post_content_filtered, guid, menu_order) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(postsSql, (1, now, now, "[job_detail_text]", datas['title'], datas['jobDesc'], "closed", datas['permaLink'], "", "", now, now, "", dtlLink, upMenuOrder))

      # "wp_postmeta"テーブルの投稿ID用に再度SELECTで取得
      postsSql = "SELECT * FROM wp_posts WHERE post_name = %s"
      cursor.execute(postsSql, (datas['permaLink']))
      postsValue = cursor.fetchone()

      # ------------------------------------------------
      # ②"wp_postmeta"テーブルにUPSERT
      # ------------------------------------------------
      scDailyValue = {
      'icon_dormitory_field': datas['dormitory'],
      'icon_highIncome_field': upIconHighIncome,
      'icon_campaign_field': datas['campaign'],
      'company_field': datas['company'],
      'occupation_field': datas['occupation'],
      'salary_field': datas['salary'],
      'term_field': datas['term'],
      'time_field': datas['time'],
      'treatment_field': datas['treatment'],
      'jobDescription_field': datas['jobDesc'],
      'affiliatelink_field': datas['affiliateLink'],
      'icon_meal_field': datas['meal'],
      'icon_transportationFee_field': datas['transportationFee'],
      'icon_wifi_field': datas['wifi'],
      'icon_spa_field': datas['spa'],
      'int_salary_field': upIntSalaryField,
      'resorn_score_field': upResornScore,
      }
      # "sc_daily"テーブルの値を1行ずつ"wp_postmeta"に格納（処理遅め）
      for pmMetaKey in scDailyValue:
        # 【改善提案】ここにstr(value[pmMetaKey])
        postmetaSql = "SELECT * FROM wp_postmeta WHERE post_id = %s AND meta_key = %s"
        cursor.execute(postmetaSql, (postsValue['ID'], pmMetaKey))
        # post_idとmeta_keyが存在するならUPDATE
        if cursor.fetchone():
          postmetaSql = "UPDATE wp_postmeta SET meta_value = %s WHERE post_id = %s AND meta_key = %s"
          cursor.execute(postmetaSql, (scDailyValue[pmMetaKey], postsValue['ID'], pmMetaKey))
        # post_idかmeta_keyが存在しないならINSERT INTO
        else:
          postmetaSql = "INSERT INTO wp_postmeta (post_id, meta_key, meta_value) VALUES (%s, %s, %s)"
          cursor.execute(postmetaSql, (postsValue['ID'], pmMetaKey, scDailyValue[pmMetaKey]))

      # ------------------------------------------------
      # ③"wp_terms"テーブルからslugに紐づくterm_idを取得
      # ------------------------------------------------
      termsSql = "SELECT * FROM wp_terms WHERE slug = %s OR slug = %s OR slug = %s OR slug = %s"
      cursor.execute(termsSql, (upCategorySlug, occupationSlug, upTaxSalary, datas['company']))
      termsValues = cursor.fetchall()

      # "wp_term_relationships"テーブルに格納されているobject_idと記事IDが同一のものを削除（⑤の処理で必要）
      termRelationshipsSql = "SELECT * FROM wp_term_relationships WHERE object_id = %s"
      cursor.execute(termRelationshipsSql, (postsValue['ID']))
      # object_idが存在するならDELETE
      if cursor.fetchone():
        termRelationshipsSql = "DELETE FROM wp_term_relationships WHERE object_id = %s"
        cursor.execute(termRelationshipsSql, (postsValue['ID']))

      # SELECTで取得した4行をそれぞれ処理
      for termsValue in termsValues:

        # ------------------------------------------------
        # ④"wp_term_taxonomy"テーブルからterm_idに紐づくterm_taxonomy_idを取得
        # ------------------------------------------------
        termTaxonomySql = "SELECT * FROM wp_term_taxonomy WHERE term_id = %s"
        cursor.execute(termTaxonomySql, (termsValue['term_id']))
        termTaxonomyValue = cursor.fetchone()

        # ------------------------------------------------
        # ⑤"wp_term_relationships"テーブルをUPSERT処理（object_idに基づきterm_taxonomy_idを追加・更新）
        # ------------------------------------------------
        # "wp_term_relationships"テーブルにobject_idとterm_taxonomy_idをINSERT
        termRelationshipsSql = "INSERT INTO wp_term_relationships VALUES (%s, %s, 0)"
        cursor.execute(termRelationshipsSql, (postsValue['ID'], termTaxonomyValue['term_taxonomy_id']))

      # ------------------------------------------------
      # ⑥"wp_posts"テーブルに画像情報をUPSERT
      # ------------------------------------------------
      # 画像へのリンクを変数に格納
      upImagePermaLink = settings.SAVE_IMAGE_PERMALINK_PATH + datas['company'] + "/" + datas['permaLink'] + ".jpg"
      # post_nameが存在するか確認する
      postsImageSql = "SELECT * FROM wp_posts WHERE post_name = %s"
      cursor.execute(postsImageSql, (datas['permaLink'] + ".jpg"))
      # post_nameが存在しないならINSERT（存在する場合は何もしない）
      if not cursor.fetchone():
        postsImageSql = "INSERT INTO wp_posts (post_author, post_date, post_date_gmt, post_content, post_title, post_status, comment_status, ping_status, post_name, post_modified, post_modified_gmt, post_parent, guid, menu_order, post_type, post_mime_type) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(postsImageSql, (1, now, now, "", datas['permaLink'] + ".jpg", "publish", "closed", "closed", datas['permaLink'] + ".jpg", now, now, postsValue['ID'], upImagePermaLink, 0, "attachment", "image/jpeg"))
      # "wp_postmeta"テーブルの画像ID用に再度SELECTで取得
      postsImageSql = "SELECT * FROM wp_posts WHERE post_name = %s"
      cursor.execute(postsImageSql, (datas['permaLink'] + ".jpg"))
      postsImageValue = cursor.fetchone()
      # ------------------------------------------------
      # ⑦"wp_postmeta"テーブルに_thumbnail_idをINSERT（存在する場合は何もしない）
      # ------------------------------------------------
      postmetaThumbSql = "SELECT * FROM wp_postmeta WHERE post_id = %s AND meta_key = %s AND meta_value = %s"
      cursor.execute(postmetaThumbSql, (postsValue['ID'], "_thumbnail_id", postsImageValue['ID']))
      if not cursor.fetchone():
        postmetaThumbSql = "INSERT INTO wp_postmeta (post_id, meta_key, meta_value) VALUES (%s, %s, %s)"
        cursor.execute(postmetaThumbSql, (postsValue['ID'], "_thumbnail_id", postsImageValue['ID']))
      # ------------------------------------------------
      # ⑧"wp_postmeta"テーブルに_wp_attached_fileをINSERT（存在する場合は何もしない）
      # ------------------------------------------------
      postmetaThumbSql = "SELECT * FROM wp_postmeta WHERE post_id = %s AND meta_key = %s AND meta_value = %s"
      followUploadsPath = "crawled-images/" + datas['company'] + "/" + datas['permaLink'] + ".jpg"
      cursor.execute(postmetaThumbSql, (postsImageValue['ID'], "_wp_attached_file", followUploadsPath))
      if not cursor.fetchone():
        postmetaThumbSql = "INSERT INTO wp_postmeta (post_id, meta_key, meta_value) VALUES (%s, %s, %s)"
        cursor.execute(postmetaThumbSql, (postsImageValue['ID'], "_wp_attached_file", followUploadsPath))

      # オートコミットじゃないので、明示的にコミットを書く必要がある
      conn.commit()
      print("「" + datas['permaLink'] + "」の格納完了(^^)やったぜ！")
    except:
      print("「" + datas['permaLink'] + "」の格納失敗！")
      dV.exception_error_log()
    finally:
      conn.close()