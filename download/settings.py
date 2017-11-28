import os

TRENDS_URL = "http://sina.aicai.com/jczq/"
RESULTS_URL = 'http://sina.aicai.com/lotnew/\
jc/getMatchByDate.htm?lotteryType=jczq&cate=gd&dataStr={date}'

try:
    DB_USER = os.environ['SOCCER_DB_USER']
    DB_PASS = os.environ['SOCCER_DB_PASS']
    DB_HOST = os.environ['SOCCER_DB_HOST']
    DB_NAME = os.environ['SOCCER_DB_NAME']
except KeyError as e:
    print("请在环境变量中设置数据库信息: ", e)
    exit()
