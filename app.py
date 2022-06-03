from flask import Flask
from flask_apscheduler import APScheduler
import config
import requests
import json
import time
from bs4 import BeautifulSoup

app = Flask(__name__)

app.debug = True
app.config['SECRET_KEY'] = config.app_secret_key
app.config['BASE_URL'] = config.base_url
app.config['API_URL'] = config.api_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)

@scheduler.task('interval', id='scrape_upcoming_games', seconds=86400)
def scrape_upcoming_games():
    week = 1
    year = 2022
    url = f'https://www.espn.com/nfl/schedule/_/week/{week}'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
    for i in range(100):
        try:
            results = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
        else:
            break
    else:
        print(f'Unable to scrape schedule. Please try again later.')

    soup = BeautifulSoup(results.text, 'html.parser')
    schedule_container = soup.find('div', {'id': 'sched-container'})
    days = schedule_container.find_all('h2', {'class': 'table-caption'})
    game_groups = schedule_container.find_all('div', {'class': 'responsive-table-wrap'})
    if len(days) != len(game_groups):
    	print('Error, length of days and game groups is not equal!')
    	return

    result = []
    for i in range(len(days)):
    	date = days[i].text
    	games = game_groups[i].find('tbody').find_all('tr')
    	for game in games:
    		teams = game.find_all('abbr')
    		away_team = teams[0].text
    		home_team = teams[1].text
    		time = game.find('td', {'data-behavior': 'date_time'})['data-date']
    		result.append(
    			{
    				'time': time,
    				'home_team': home_team,
    				'away_team': away_team,
    				'year': year,
    				'week': week
    			}
    		)
    requests.post(app.config['API_URL'], {'games': result})
	
if __name__ == '__main__':
	scheduler.start()
	app.run(host='127.0.0.1', port=8000, use_reloader=False)
	app.run()


