"""Аутентификация приложения

Получение request_token, access_token"""

import json
import os
import sys
import webbrowser
from pprint import pprint

import requests

consumer_key_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/consumer_key.json')
request_token_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/request_token.json')
access_token_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/access_token.json')

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

headers = {
    'Content-Type': 'application/json; charset=UTF8',
    'X-Accept': 'application/json'
}


class ResponseContentError(Exception):
    pass


def response_is_valid(response: requests.Response):
    """
    Args:
        response (requests.Response):
    """
    try:
        return response.json()
    except ValueError as e:
        print(e)
        pprint(response.headers, indent=2)
        sys.exit()


def get_request_token(header: dict, post_data_json: dict) -> dict:
    """Получить токен запроса

    Токен запроса используется для предоставления приложению прав для доступа
    к данным пользователя.

    Args:
        header (dict): заголовки для request
        post_data_json (dict): dict(consumer_key:string, redirect_uri: string}

    Returns:
        Строка с request token либо пустую строку
    """
    url = 'https://getpocket.com/v3/oauth/request'
    r = requests.request('post', url, json=post_data_json, headers=header)

    return response_is_valid(r)


def get_access_token(header: dict, consumer_key: str, code: str) -> dict:
    """Получить токен доступа

    Потом токен доступа используется для запросов используя API

    Args:
        header (dict): заголовки для request
        consumer_key (str): consumer key
        code (str): request_token

    Returns:
        Словарь с access_token и username
    """
    # привязка к аккаунту гугл
    url = 'http://getpocket.com/auth/authorize?request_token={0}' \
          '&redirect_uri={1}'.format(code, 'http://google.com')
    webbrowser.open_new_tab(url)

    url = 'https://getpocket.com/v3/oauth/authorize'
    r = requests.request('post', url,
                         json={'consumer_key': consumer_key, 'code': code},
                         headers=header)

    return response_is_valid(r)


def app_authentication():
    """Аутентификация приложения, получение токенов"""
    with open(consumer_key_file) as f:
        consumer_json = json.load(f)
    request_token = get_request_token(headers, consumer_json)
    with open(request_token_file, 'w') as f:
        json.dump(request_token, f, indent=2, ensure_ascii=False)
    code = request_token['code']
    access_token = get_access_token(headers, consumer_key=CONSUMER_KEY, code=code)
    with open(access_token_file, 'w') as f:
        json.dump(access_token, f, indent=2, ensure_ascii=False)

    global ACCESS_TOKEN
    ACCESS_TOKEN = access_token['access_token']


if __name__ == '__main__':
    app_authentication()
