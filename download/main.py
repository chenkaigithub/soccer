import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json
from datetime import datetime

import dryscrape
import requests
from bs4 import BeautifulSoup
from sqlalchemy.exc import OperationalError

import download.parser as parser
from download import storage
from download.settings import *


def get_page(with_js=False):
	print('正在加载网页{}读取数据...'.format(TRENDS_URL))
	if with_js:
		session = dryscrape.Session()
		session.visit(TRENDS_URL)
		page = session.body()
	else:
		response = requests.get(TRENDS_URL)
		if response.status_code == 200:
			print('网页加载成功!\n')
		else:
			print('网页错误, 加载失败\n')
			return None
		page = response.content
	soup = BeautifulSoup(page, 'html.parser')
	return soup


def get_trends():
	page = get_page()
	print('正在分析网页内容...')
	games = page.find_all('tr', class_='jq_gdhhspf_match_select_tr')
	print('分析结束, 共找到{}场赛事\n'.format(len(games)))

	print('开始提取比赛数据...')
	data = []
	for game in games:
		result = parser.parse_game(game)
		data.append(result)
	print('数据提取完成\n')
	return data


def get_results():

	def _construct_url(date):
		return RESULTS_URL.format(date=date)

	print('开始请求比赛结果数据...')
	page = get_page(with_js=True)
	selector = page.find('select', id='jq_change_term')
	options = selector.find_all('option')
	results = []
	for option in options:
		date = option['value']
		if '当前' in date:
			continue
		url = _construct_url(date)
		data = str(requests.get(url).content, 'utf8')
		data = data.replace('\'', '\"')
		result_dict = json.loads(data)
		results += parser.parse_results(result_dict)
	print('比赛结果数据提取结束, 共找到{}场比赛结果\n'.format(len(results)))
	return results


def is_every_n_minutes(time, n_minutes):
	if time.second != 0 or time.microsecond != 0:
		return False
	if time.minute % n_minutes == 0:
		return True
	return False


if __name__ == '__main__':
	try:
		storage.init_database()
	except OperationalError as oe:
		print("数据库初始化错误: {}".format(oe))
		print("程序及将终止")
		exit()

	while True:
		current = datetime.now()
		if is_every_n_minutes(current, 5):
			print(">> 当前时间: ", current)

			data = get_trends()
			try:
				storage.save_game_trends(data)
			except Exception as e:
				print('[ERROR] 未知错误 ({}): '.format(type(e).__name__), e)

		if is_every_n_minutes(current, 60):
			print(">> 当前时间: ", current)

			results = get_results()
			try:
				storage.save_game_results(results)
			except Exception as e:
				print('[ERROR] 未知错误 ({}): '.format(type(e).__name__), e)

