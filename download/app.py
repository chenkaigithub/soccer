# -*- coding: utf8 -*-
import os
import sys
from time import sleep

import json
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from sqlalchemy.exc import OperationalError

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import download.parser as parser
from download import storage
from download.settings import *

def get_page():
	print('正在加载网页{}读取数据...'.format(TRENDS_URL))

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
	results = []
	today = datetime.now().date()
	for i in range(1, 7):
		date = today - timedelta(days=i)
		date_str = str(date).replace('-', '').replace('201', '1')

		url = _construct_url(date_str)
		response = str(requests.get(url).content, 'utf8')
		data = response.replace('\'', '\"')

		result_dict = json.loads(data)
		results += parser.parse_results(result_dict)
	print('比赛结果数据提取结束, 共找到{}场比赛结果\n'.format(len(results)))
	return results


def is_punctual():
	is_punctual.ticked = False

	def check(time):
		if time.minute == 0 and not is_punctual.ticked:
			is_punctual.ticked = True
			return True
		elif time.minute != 0:
			is_punctual.ticked = False
		return False

	return check


def is_every_n_minutes(n_minutes):
	fired = False
	def check(time):
		nonlocal fired
		if time.minute % n_minutes == 0 and not fired:
			fired = True
			return True
		elif time.minute % n_minutes != 0:
			fired = False
		return False
	return check


def main():
	try:
		storage.init_database()
	except OperationalError as oe:
		print("数据库初始化错误: {}".format(oe))
		print("程序及将终止")
		exit()

	trend_frequency = is_every_n_minutes(5)
	result_frequency = is_every_n_minutes(60)

	while True:

		current = datetime.now()

		if trend_frequency(current):
			print(">> 当前时间: ", current)
			data = get_trends()
			try:
				storage.save_game_trends(data)
			except Exception as e:
				print('[ERROR] 未知错误 ({}): '.format(type(e).__name__), e)

		if result_frequency(current):
			print(">> 当前时间: ", current)
			results = get_results()
			try:
				storage.save_game_results(results)
			except Exception as e:
				print('[ERROR] 未知错误 ({}): '.format(type(e).__name__), e)

		sys.stdout.flush()
		sleep(10)


def run_once():
	try:
		storage.init_database()
	except OperationalError as oe:
		print("数据库初始化错误: {}".format(oe))
		print("程序及将终止")
		exit()

	data = get_trends()
	try:
		storage.save_game_trends(data)
	except Exception as e:
		print('[ERROR] 未知错误 ({}): '.format(type(e).__name__), e)
	results = get_results()
	storage.save_game_results(results)


if __name__ == '__main__':
	main()