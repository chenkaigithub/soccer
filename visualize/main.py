# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from download.storage import *
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

if __name__ == '__main__':
	global engine
	url = db_url()
	engine = create_engine(url, echo=False)
	session = Session(bind=engine)

	games = session.query(Game).filter(Game.serial >= '20170817001').all()[:5]

	for i, game in enumerate(games):
		plt.figure(i)
		dataset = game.points

		wins = []; draws = []; loses = []

		for data in dataset:
			wins.append(data.win)
			draws.append(data.draw)
			loses.append(data.lose)


		x = range(len(wins))
		plt.plot(x, wins)
		plt.plot(x, draws)
		plt.plot(x, loses)

		plt.legend([u'胜', u'平', u'负'], loc='upper left')
		plt.title("{} {}:{}".format(game.serial, game.host, game.guest))
	plt.show()
