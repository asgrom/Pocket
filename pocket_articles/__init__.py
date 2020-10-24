"""Пакет для просмотра, импорта сохраненных статей

Импортирует сохраненные html страницы из выбранного каталога. Импорт происходит в базу данных.
"""
import json
import os
import sys

consumer_key_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/consumer_key.json')
request_token_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/request_token.json')
access_token_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/access_token.json')
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/articles.db')


try:
    with open(access_token_file) as fn:
        ACCESS_TOKEN = json.load(fn)['access_token']
except OSError as e:
    print('Неоходимо получить access_token\n', e)
    sys.exit()

try:
    with open(consumer_key_file) as fn:
        CONSUMER_KEY = json.load(fn)['consumer_key']
except OSError as e:
    print('Необходим consumer_key\n', e)
    sys.exit()
