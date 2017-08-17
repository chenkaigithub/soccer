import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.exc import OperationalError

from download import storage
from download.main import get_trends, get_results

if __name__ == '__main__':
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
