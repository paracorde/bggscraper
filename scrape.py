from login import login_cookies

import scrapy
from xml.etree import ElementTree
import pandas as pd
import os
import json
import time

START = 331
VOTER_THRESHOLD = 25
class DSpider(scrapy.Spider):
    name = 'DSpider'
    base_url = 'https://boardgamegeek.com/browse/boardgame/page/{n}?sort=numvoters&sortdir=desc'
    start_urls = [base_url.format(n=START)]
    api_endpoint = 'https://boardgamegeek.com/xmlapi/'

    def __init__(self, *args, **kwargs):
        self.cookies = login_cookies()
        super().__init__(*args, **kwargs)
        self.csv_filename = 'boardgame_data.csv'
        self.columns = [
            'game_id', 'name', 'year_published', 'min_players', 'max_players',
            'playing_time', 'min_playing_time', 'max_playing_time', 'age', 'description',
            'voters', 'average_score', 'owned', 'trading', 'wanting', 
            'wishing', 'comments', 'average_weight', 'categories', 'types'
        ]

        if os.path.exists(self.csv_filename):
            self.df = pd.read_csv(self.csv_filename)
        else:
            self.df = pd.DataFrame(columns=self.columns)
        self.current = START
    
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, cookies={cookie['name']: cookie['value'] for cookie in self.cookies})

    def parse(self, response):
        rows = response.css('tr[id="row_"]')
        if not rows:
            self.logger.info(f"Rate limit detected on page {self.current}. Retrying after 5 seconds... ")
            time.sleep(5)
            yield scrapy.Request(
                url=response.url, 
                callback=self.parse,
                dont_filter=True
            )
            return
        for row in rows:
            try:
                nv = int(row.css('td.collection_bggrating')[2].css('::text').get())
                if nv < VOTER_THRESHOLD: return
            except ValueError:
                return
            game_id = row.css('a.primary::attr(href)').get().split('/')[2]
            yield response.follow(DSpider.api_endpoint + 'boardgame/' + game_id + '?&stats=1', callback=self.parse_game, meta={'game_id': game_id})
        self.current = self.current + 1
        yield scrapy.Request(DSpider.base_url.format(n=self.current))
    
    def parse_game(self, response):
        data = {'game_id': response.meta['game_id']}

        root = ElementTree.fromstring(response.text)
        game = root.find('boardgame')
        stats = game.find('statistics/ratings')

        data['name'] = game.find(".//name[@primary='true']").text or game.findtext('name')
        data['year_published'] = game.findtext('yearpublished')
        data['min_players'] = game.findtext('minplayers')
        data['max_players'] = game.findtext('maxplayers')
        data['playing_time'] = game.findtext('playingtime')
        data['min_playing_time'] = game.findtext('minplaytime')
        data['max_playing_time'] = game.findtext('maxplaytime')
        data['age'] = game.findtext('age')
        data['description'] = game.findtext('description')

        data['voters'] = stats.findtext('usersrated')
        data['average_score'] = stats.findtext('average')
        data['owned'] = stats.findtext('owned')
        data['trading'] = stats.findtext('trading')
        data['wanting'] = stats.findtext('wanting')
        data['wishing'] = stats.findtext('wishing')
        data['comments'] = stats.findtext('numcomments')
        data['average_weight'] = stats.findtext('averageweight')

        data['categories'] = ';'.join([cat.text for cat in game.findall('boardgamecategory')])
        data['types'] = []
        ranks = stats.find('ranks')
        for rank in ranks.findall('rank'):
            if rank.get('type') in {'family', 'subtype'}:
                data['types'].append(rank.get('name').removesuffix('games'))
        data['types'] = ';'.join(data['types'])
        next_row = pd.DataFrame([data], columns=self.columns)
        self.df = pd.concat([self.df, next_row], ignore_index=True)

        yield data

    def closed(self, reason):
        self.df.to_csv('boardgame_data.csv', index=False)