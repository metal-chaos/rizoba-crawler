# coding: UTF-8
import traceback,sys
from time import sleep
import datetime
import connection

def resorn_score(dormitory, campaign, meal, transportationFee, wifi, spa, KindOfSalary, figureOfsalary):
  sum_resorn_score = 0
  welfares = [dormitory, campaign, meal, transportationFee, wifi, spa]
  for welfare in welfares:
    if welfare == "TRUE":
      sum_resorn_score += 0.5
  if "時給" in KindOfSalary:
    if 1000 < figureOfsalary and figureOfsalary <= 1100:
      sum_resorn_score += 0.5
    elif 1100 < figureOfsalary and figureOfsalary <= 1200:
      sum_resorn_score += 1
    elif 1200 < figureOfsalary and figureOfsalary <= 1300:
      sum_resorn_score += 1.5
    elif 1300 < figureOfsalary:
      sum_resorn_score += 2
  return sum_resorn_score

aa = resorn_score("FALSE", "TRUE", "TRUE", "TRUE", "TRUE", "TRUE", "時給", 1080)
print(aa)