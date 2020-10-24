"""Предоставляе методы для получения данных о сохранненых статьях с сервиса getpocket.com"""
import sys
import webbrowser

from pocket import Pocket, PocketException

from . import CONSUMER_KEY, ACCESS_TOKEN

pocket_json_data = {}  # данные с getpocket


def open_articles_in_browser(data: dict):
    """Открывает страницы из Pocket

    В описании каждой статьи сохранен урл, по которому она находится. Метод
    открывает их в браузере по 5 штук, чтобы их можно было сохранить.

    Args:
        data (dict):
    """
    i = 0
    for article in data['list'].values():
        webbrowser.open_new_tab(article['given_url'])
        i += 1
        if i == 5:
            i = 0
            input('Press any key')


def get_pocket_data(since=None, state=None, tag=None):
    """Получить json данные с getpocket

    Данные о сохраненных страницах в Pocket. tag - можно задать для поиска
    статей по определенному тегу.

    Args:
        since:
        state:
        tag:
    """
    try:
        p = Pocket(consumer_key=CONSUMER_KEY, access_token=ACCESS_TOKEN)
        return p.retrieve(since=since, state=state, tag=tag, detailType='complete')
    except PocketException as e:
        print(e)
        sys.exit()
