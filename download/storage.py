import json
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import TIMESTAMP
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from download.settings import *


def db_url():
	url_base = '{dialect}+{driver}://{username}:{password}@{host}/{db}?charset=utf8'
	url = url_base.format(
		dialect='mysql', driver='mysqldb',
		username=DB_USER, password=DB_PASS,
		host=DB_HOST, db=DB_NAME)
	return url


Base = declarative_base()
engine = None
Session = sessionmaker()

class Game(Base):
	__tablename__ = 'game'

	id = Column(Integer, primary_key=True)
	serial      = Column(String(11), unique=True, index=True)
	league      = Column(String(16))
	deadline    = Column(DateTime)
	host        = Column(String(20))
	guest       = Column(String(20))
	endorse     = Column(Integer)
	concede     = Column(Integer)
	host_score  = Column(Integer)
	guest_score = Column(Integer)

	points = relationship('GameOdds', back_populates='game')

	def __str__(self):
		return "<比赛{} {}:{} 让{}球 db_id:{}>".format(self.serial, self.host, self.guest, self.concede, self.id)

	def result(self):
		return "<比赛{}结果 {}:{}>".format(self.serial, self.host_score, self.guest_score)


class GameOdds(Base):
	__tablename__ = 'game_odds'

	id = Column(Integer, primary_key=True)
	game_id = Column(Integer, ForeignKey('game.id'))
	record_time = Column(DateTime, default=datetime.now)
	win = Column(Float(5))
	draw = Column(Float(5))
	lose = Column(Float(5))
	cwin = Column('concede_win', Float(5))
	cdraw = Column('concede_draw', Float(5))
	close = Column('concede_lose', Float(5))

	game = relationship('Game', back_populates='points')

	def __repr__(self):
		return "<比赛实时赔率 {serial} {time} {w1}:{d1}:{l1}/{w2}:{d2}:{l2}>".format(
			serial=self.game.serial,
			time=self.record_time,
			w1=self.win, d1=self.draw, l1=self.lose,
			w2=self.cwin, d2=self.cdraw, l2=self.close
		)


def init_database(echo=False):
	print('正在初始化数据库...')
	global engine
	url = db_url()
	engine = create_engine(url, echo=echo)
	Base.metadata.create_all(engine)
	global Session
	Session.configure(bind=engine)
	print('初始化完成\n')


def save_game_trends(game_list):

	def unpack(data):
		base = data.copy()
		del base['odds'], base['codds']
		year, month, day = data['serial'][:4], data['serial'][4:6], data['serial'][6:8]
		time = data['deadline']
		deadline = datetime.strptime("{}-{}-{} {}".format(year, month, day, time), '%Y-%m-%d %H:%M')
		base['deadline'] = deadline

		if data['odds'] is None:
			data['odds'] = [0, 0, 0]

		if data['codds'] is None:
			data['codds'] = [0, 0, 0]

		odds = {
			'win': data['odds'][0],
			'draw': data['odds'][1],
			'lose': data['odds'][2],
			'cwin': data['codds'][0],
			'cdraw': data['codds'][1],
			'close': data['codds'][2]
		}

		return base, odds

	print("正在储存实时比赛数据...")
	session = Session()
	num_game = 0
	num_rt = 0
	for game_data in game_list:
		try:
			game_base, game_odds = unpack(game_data)
		except Exception as error:
			print('[ERROR] 数据格式不完整: ', error)
			print('源数据: ', json.dumps(game_data, indent=4, ensure_ascii=False))
			print('跳过该项')
			continue
		game = Game(**game_base)

		result = session.query(Game).filter(Game.serial == game.serial).first()
		if result is None:
			session.add(game)
			session.commit()
			game_id = game.id
			num_game += 1
		else:
			game = result
			game_id = result.id
		game_odds['game_id'] = game_id
		real_time = GameOdds(**game_odds)
		real_time.game = game
		session.add(real_time)
		session.commit()
		num_rt += 1
	print('储存结束, 已存比赛信息{}场, 实时赔率数据{}组\n'.format(num_game, num_rt))


def save_game_results(game_list):
	print('正在储存比赛结果数据...')
	session = Session()
	num_games = 0
	for game_data in game_list:
		# print(json.dumps(game_data, indent=4, ensure_ascii=False))
		serial = game_data['serial']
		result = session.query(Game).filter(Game.serial == serial).first()
		if result:
			result.host_score = game_data['host_score']
			result.guest_score = game_data['guest_score']
			num_games += 1
	session.commit()
	print('储存结束, 共更新{}场比赛结果信息\n'.format(num_games))


if __name__ == '__main__':
	time1 = datetime(2017, 8, 15, 12, 52)
	current = datetime.now()
	delta = current - time1
	print(delta.total_seconds() // 60 // 60)
