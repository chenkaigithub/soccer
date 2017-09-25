import re


def get_game_date(game):
	_table = game.parent
	game_date_raw = _table.find('td', class_='gameTime').text

	p = re.compile(r'\d{4}-\d{02}-\d{2}')
	date = p.findall(game_date_raw)
	if not len(date):
		return None
	date = date[0]
	return date.replace('-', '')


def get_endorsement(game):
	endorse = game.find('span', class_='zhuanSpan')
	if not endorse:
		return None
	endorse = endorse.text
	p = re.compile(r'\d+')
	endorse = p.findall(endorse)
	return 0 if not len(endorse) else endorse[0]


def get_concede(game):
	panels = game.find_all('div', class_='betPanel')
	if len(panels) != 2:
		return None
	panel = panels[1]
	concede = panel.find('div', class_='rqMod')
	if not concede:
		return None
	return int(concede.text)


def get_odds(game, with_concede=False):
	panels = game.find_all('div', class_='betPanel')
	if len(panels) != 2:
		return None

	panel = panels[1 if with_concede else 0]
	odds = panel.find_all('div', class_='betChan')
	if len(odds) != 3:
		return None
	return [float(i.text) for i in odds]


def parse_game(game):
	date = get_game_date(game)
	if not date:
		return None
	game_id = game.find('a', class_='jq_gdhhspf_selectmatch')
	if not game_id:
		return None
	game_id = game_id.text
	serial_number = date + game_id
	cup = game.find('td', class_='saiTd')
	if not cup:
		cup = None
	else:
		cup = cup.text
	deadline = game.find('td', class_='stopTd jq_gdhhspf_match_changetime')
	if not deadline:
		return None
	deadline = deadline.text
	host = game.find('td', class_='zhuTeamTd').text
	guest = game.find('td', class_='keTeamTd').text
	num_endorse = get_endorsement(game)
	concede = get_concede(game)
	odds = get_odds(game, with_concede=False)
	codds = get_odds(game, with_concede=True)
	return {
		'serial': serial_number,
		'league': cup,
		'deadline': deadline,
		'host': host,
		'guest': guest,
		'endorse': num_endorse,
		'concede': concede,
		'odds': odds,
		'codds': codds
	}


def parse_results(result_dict):
	game_date = result_dict['weekDate'].replace('-', '')
	games = result_dict['raceList']
	results = []
	for game_id in games:
		serial_number = game_date + game_id
		score_raw = games[game_id]['wholeScore']
		if len(score_raw) > 0:
			if ':' not in score_raw:
				continue
			host, guest = score_raw.split(':')
			results.append({
				'serial': serial_number,
				'host_score': host,
				'guest_score': guest
			})
	return results
